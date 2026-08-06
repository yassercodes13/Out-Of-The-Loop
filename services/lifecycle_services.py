from adapters.telegram.messaging import broadcast_message, edit_message, send_info_message
from data.users import get_user_by_id
from data.games import delete_game, make_game, get_game_by_id
from data.sessions import delete_session, get_session_by_id, make_session
from data.links import get_session_of_owner, link_session_and_game, link_user_and_game
from flows.states import GameState, mid_game_states
from flows.substates import SetupSubstate
from flows.utils import set_all_substates
from models.game import Game
from models.session import Session
from models.user import User
from views.paused import render_paused_screen
from views.setup import render_choose_mode_screen
from views.common import (
  render_player_left_game_terminated_screen,
  render_owner_left_game_screen,
  render_you_became_owner_screen,
  render_player_left_choose_mode_screen,
  render_player_left_waiting_owner_screen,
  render_player_left_ready_to_continue_screen,
)

async def create_game(owner: User, owner_session: Session):
  if not owner or not owner_session: return None

  game = make_game(owner_id = owner.id, owner_session_id = owner_session.id)
  link_user_and_game(owner, game)
  link_session_and_game(owner_session, game)

  return game

async def terminate_game(game: Game = None):
  if not game:
    return None
    
  for sid in game.session_ids:
    await terminate_session(session_id = sid)
  
  for user_id in game.user_ids:
    user = await get_user_by_id(user_id)
    if user:
      user.game_id = None

  if game.reminder:
    game.reminder.schedule_removal()
    game.reminder = None
    
  return delete_game(game)

async def set_session(id: int, message_id: int, user_id: int, bot, job_queue, game_id: str | None = None, game_substate: str | None = None):
  old_session = get_session_by_id(id)
  if old_session:
    await terminate_session(session_id = old_session.id)
  
  new_session = make_session(id, message_id, user_id, bot, job_queue, game_id, game_substate)

  game = get_game_by_id(game_id)
  if game:
    link_session_and_game(new_session, game)

  return new_session

async def terminate_session(session_id: int = None):

  if not session_id: return

  session = get_session_by_id(session_id)
  
  if session:
    if session.reminder:
      session.reminder.schedule_removal()
    if session.user_id:
      user = await get_user_by_id(session.user_id)
      user.game_id = None
    
    game = get_game_by_id(session.game_id)
    if game and session.id in game.session_ids:
      game.session_ids.remove(session.id)

  return delete_session(session)

async def remove_players(game: Game, player_ids: list[int]):
  """Single entry point for leave / kick / timeout. Caller decides which
  player_ids to remove; this only handles the consequences."""

  # --- 1: figure out affected sessions before we mutate anything ---
  affected_session_ids = {
    p.session_id for p in game.players if p.id in player_ids
  }
  players_names = ", ".join([game.get_player_by_id(pid).name for pid in player_ids])

  # --- 2: remove the players, then check which sessions are now empty ---
  for pid in player_ids:
    game.remove_player(pid)

  emptied_sessions: list[Session] = []
  for session_id in affected_session_ids:
    session = get_session_by_id(session_id)
    if not session: continue

    session.players = [p for p in session.players if p.id not in player_ids]
    if not session.players:
      emptied_sessions.append(session)

  # --- 3: ownership transfer, before we notify anyone ---
  owner_left = any(s.user_id == game.owner_id for s in emptied_sessions)

  for session in emptied_sessions:
    await terminate_session(session_id = session.id)
  
  #TODO: With better joining logic this could be recoverable
  if (game.state == GameState.SETUP) or (not game.session_ids):
    screen = render_player_left_game_terminated_screen(players_names if player_ids != [] else None)

    await broadcast_message(game, "send", screen.textref)
    await terminate_game(game)
    return
  
  if owner_left and game.session_ids:
    await _reassign_ownership(game)

  # --- 4: abandon whatever round was in progress ---
  if game.state in mid_game_states:
    game.round_number -= 1
  game.reset_round()
  set_all_substates(game, None, set_waited=False)

  owner_session = get_session_of_owner(game=game)
  if not owner_session:
    return

  # --- 5: recalculate and route to the right recovery screen ---
  if len(game.players) < 3:
    game.state = GameState.PAUSED
    # Use the view to build the screen
    screen = render_paused_screen(len(game.players))
    owner_session = get_session_of_owner(game=game)
    if owner_session:
      owner_session.waited = False
      await broadcast_message(
        game=game,
        mode="edit",
        text=screen.textref,
        exclude_session_ids=[owner_session.id]
      )
      await edit_message(owner_session, screen.textref, screen.buttons)
    return

  if game.mode and game.min_players > len(game.players):
    owner = get_user_by_id(game.owner_id)
    await _restart_mode_selection(game, owner)
  else:
    await _confirm_round_continuation(game, owner_session, players_names)


async def _reassign_ownership(game: Game):
  """"If the owner left, inform the new owner and update the game state accordingly."""

  screen = render_owner_left_game_screen()
  await broadcast_message(game, "send", screen.textref)

  if not game.session_ids: return
  new_owner_session = get_session_by_id(game.session_ids[0])
  if not new_owner_session: return
  new_owner = await get_user_by_id(new_owner_session.user_id)

  game.owner_id = new_owner_session.user_id
  game.owner_session_id = new_owner_session.id
  game.random_mode_options =  new_owner.random_modes

  screen = render_you_became_owner_screen()
  await send_info_message(
    bot = new_owner_session.bot,
    chat_id = new_owner_session.id,
    text = screen.textref,
    lang = new_owner.lang
  )

async def _restart_mode_selection(game: Game, user: User):
  """If the mode is no longer valid due to player departures, make the owner choose a new mode."""

  game.state = GameState.SETUP
  owner_session = get_session_of_owner(game=game)
  if not owner_session: return

  set_all_substates(game, None, set_waited=False, exclude_session_ids=[owner_session.id])
  owner_session.game_substate = SetupSubstate.CHOOSE_MODE

  # Use the view, then edit the message
  screen = render_choose_mode_screen(user, category_info="", mode_change=True)
  await edit_message(owner_session, screen.textref, screen.buttons)

  screen = render_player_left_choose_mode_screen()
  await broadcast_message(
    game = game, mode="edit",
    text = screen.textref,
    exclude_session_ids=[owner_session.id]
  )

async def _confirm_round_continuation(game: Game, owner_session: Session, players_names: str):
  """If the game is in a state where the mode is still valid, make the owner confirm before continuing."""
 
  game.state = GameState.INFORM
  owner_session.game_substate = None
 
  owner_session.waited = True
  waiting_screen = render_player_left_waiting_owner_screen(players_names)
  await broadcast_message(
    game = game, mode = "edit",
    text = waiting_screen.textref,
    exclude_session_ids = [owner_session.id]
  )
 
  continue_screen = render_player_left_ready_to_continue_screen(players_names)
  await edit_message(owner_session, continue_screen.textref, continue_screen.buttons)