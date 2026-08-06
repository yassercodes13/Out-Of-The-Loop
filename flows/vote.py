from models.modes import GameMode
from flows.states import GameState
from flows.substates import VoteSubstate
from telegram import Update
from flows.utils import reset_turn_indices, set_all_substates
from models import Game, Session
from adapters.telegram.messaging import edit_message, broadcast_message
from data.links import get_session_of_owner
from texts.refs import BroadcastScreens
from views.vote import (
  render_start_vote_broadcast,
  render_select_vote_screen,
  render_confirm_vote_screen,
  render_end_vote_screen,
)


async def handle_voting(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data

  # --- INITIALIZE ---
  if data == 'g:start_vote':
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteSubstate.SELECT, set_waited=True)

    # Broadcast start screen to others (with 'Start Voting' button)
    screen = render_start_vote_broadcast(session.text)
    await broadcast_message(
      game=game,
      mode="edit",
      text=screen.textref,
      buttons=screen.buttons
    )
    return False

  elif data == 'g:revote':
    session.game_substate = VoteSubstate.SELECT

  elif data == "g:reveal" and session.game_substate == VoteSubstate.END:
    game.count_votes()
    game.state = GameState.REVEAL
    set_all_substates(game, None, set_waited=False)
    return True

  # --- confirmation ---
  if data == "g:confirm" and session.game_substate == VoteSubstate.CONFIRM:
    voter = session.players[session.turn_index]
    voter.confirm_vote()
    session.turn_index += 1
    session.game_substate = VoteSubstate.SELECT

    # --- END CONDITION (all players in this session voted) ---
    if session.turn_index >= len(session.players):
      session.game_substate = VoteSubstate.END
      game.sessions_ready += 1
      session.waited = False

      all_ready = (game.sessions_ready >= len(game.session_ids))
      is_owner = (session.user_id == game.owner_id)

      # Determine reveal button key based on mode
      if game.mode == GameMode.TEAMS and game.detective:
        reveal_key = "reveal_detective"
      elif game.mode == GameMode.TEAMS:
        reveal_key = "reveal_teams"
      else:
        reveal_key = "reveal_outsider"

      result = render_end_vote_screen(all_ready, reveal_key)

      if isinstance(result, BroadcastScreens):
        # Owner gets special screen with button, others get text only
        owner_session = get_session_of_owner(game=game)
        owner_session.waited = True
        await edit_message(owner_session, result.special.textref, result.special.buttons)
        # Broadcast to others (exclude owner)
        await broadcast_message(
          game=game,
          mode="edit",
          text=result.others.textref,
          exclude_session_ids=[owner_session.id]
        )
      else:
        # Not all ready: everyone sees the same waiting screen
        await edit_message(session, result.textref, result.buttons)

      return False

  # --- handle vote selection ---
  if data.startswith("g:vote_") and session.game_substate == VoteSubstate.SELECT:
    voter = session.players[session.turn_index]
    voted_id = int(data.replace("g:vote_", ""))
    voted_player = game.get_player_by_id(voted_id)
    voter.vote_on(voted_player)

    session.game_substate = VoteSubstate.CONFIRM
    screen = render_confirm_vote_screen(voter.name, voted_player.name)
    await edit_message(session, screen.textref, screen.buttons)
    return False

  # --- RENDER SELECT SCREEN (when entering or re-entering SELECT substate) ---
  if session.game_substate == VoteSubstate.SELECT:
    voter = session.players[session.turn_index]
    other_players = [(p.name, p.id) for p in game.players if p != voter]
    screen = render_select_vote_screen(voter.name, other_players, game.mode)
    await edit_message(session, screen.textref, screen.buttons)
    return False

  return False