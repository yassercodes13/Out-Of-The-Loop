from data.runtime_manager import get_session_of_chat, terminate_game, terminate_session, get_session_of_owner, get_user_by_id
from flows.states import GameState, mid_game_states
from flows.substates import SetupSubstate
from flows.utils import set_all_substates
from flows.setup import render_choose_mode_screen
from flows.paused import render_paused_screen
from models.game import Game
from models.session import Session
from adapters.telegram.messaging import broadcast_message, edit_message, send_info_message
from texts.refs import TextRef, Button

async def remove_players(game: Game, player_ids: list[int]):
  """Single entry point for leave / kick / timeout. Caller decides which
  player_ids to remove; this only handles the consequences."""

  # --- 1: figure out affected sessions before we mutate anything ---
  affected_chat_ids = {
    p.session_id for p in game.players if p.id in player_ids
  }
  players_names = ", ".join([game.get_player_by_id(pid).name for pid in player_ids])

  # --- 2: remove the players, then check which sessions are now empty ---
  for pid in player_ids:
    game.remove_player(pid)

  emptied_sessions: list[Session] = []
  for chat_id in affected_chat_ids:
    session = get_session_of_chat(chat_id)
    if not session:
      continue
    session.players = [p for p in session.players if p.id not in player_ids]
    if not session.players:
      emptied_sessions.append(session)


  # --- 3: ownership transfer, before we notify anyone ---
  owner_left = any(s.user_id == game.owner_id for s in emptied_sessions)

  for session in emptied_sessions:
    await terminate_session(session)
  
  if owner_left:
    if game.chat_ids:
      await broadcast_message(game, "send", TextRef("owner_left_game"))

      new_owner_session = get_session_of_chat(game.chat_ids[0])
      new_owner = await get_user_by_id(new_owner_session.user_id)

      game.owner_id = new_owner_session.user_id
      game.owner_chat_id = new_owner_session.chat_id
      game.random_mode_options =  new_owner.random_modes

      await send_info_message(
        bot = new_owner_session.bot,
        chat_id = new_owner_session.chat_id,
        text = TextRef("you_became_owner"),
        lang = new_owner.lang
      )

  #TODO: With better joining logic this could be recoverable
  if (game.state == GameState.SETUP) or (not game.chat_ids):
    await broadcast_message(game, "send", TextRef("player_left_game_terminated", {"players_names": players_names}))
    await terminate_game(game)
    return

  # --- 4: abandon whatever round was in progress ---
  game.reset_round()
  set_all_substates(game, None, set_waited=False)

  owner_session = get_session_of_owner(game=game)
  if not owner_session:
    return

  # --- 5: recalculate and route to the right recovery screen ---
  if len(game.players) < 3:
    game.state = GameState.PAUSED
    await render_paused_screen(game, owner_session)
    return


  if game.random_mode: 
    min_players = max([m.min_players for m in game.random_mode_options], default = 3)
  else:
    min_players = game.mode.min_players

  if game.mode and min_players > len(game.players):
    if game.state in mid_game_states:
      game.round_number -= 1
    game.state = GameState.SETUP
    owner_session.game_substate = SetupSubstate.CHOOSE_MODE
    set_all_substates(game, SetupSubstate.WAITING, exclude_chat_ids=[owner_session.chat_id])

    user = await get_user_by_id(owner_session.user_id)
    await broadcast_message(
      game = game, mode = "edit",
      text = TextRef("mode_no_longer_valid", {"players_names": players_names}),
      exclude_chat_ids=[owner_session.chat_id]
    )
    await render_choose_mode_screen(owner_session, user, mode_change=True)
    return

  # enough players, mode still valid — let the owner confirm before jumping back in
  if game.state in mid_game_states:
    game.round_number -= 1
  game.state = GameState.INFORM
  owner_session.game_substate = None
  buttons = [[Button(TextRef("continue"), "g:start_round")]]

  owner_session.waited = True
  await broadcast_message(
    game = game, mode = "edit",
    text = TextRef("player_left_waiting_owner", {"players_names": players_names}),
    exclude_chat_ids = [owner_session.chat_id]
  )
  await edit_message(owner_session, TextRef("player_left_ready_to_continue", {"players_names": players_names}), buttons)