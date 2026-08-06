from flows.utils import set_all_substates
from models import Game, Session
from flows.states import GameState
from flows.substates import GuessTeamsSubstate
from telegram import Update
from data.links import get_session_of_owner
from models.role import Role
from adapters.telegram.messaging import edit_message, broadcast_message
from views.guess_teams import (
  render_detective_waiting_screen,
  render_guessing_screen,
  render_result_screen,
)

async def handle_guess_teams(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  detective = game.detective
  session.waited = True

  # --- START FLOW ---
  if data == "g:guess_teams" and session.game_substate is None:
    game.sessions_ready = 0

    detective.team_guess = {
      p.id: Role.ALPHA.value for p in game.players if p != detective
    }

    session.game_substate = GuessTeamsSubstate.GUESSING
    set_all_substates(game, GuessTeamsSubstate.WAITING, exclude_session_ids=[session.id])

    # Broadcast waiting screen to others
    waiting_screen = render_detective_waiting_screen()
    await broadcast_message(
      game=game,
      mode="edit",
      text=waiting_screen.textref,
      exclude_session_ids=[session.id]
    )

    # Show guessing screen to detective
    players_info = [
      (p.id, p.name, detective.team_guess[p.id])
      for p in game.players if p != detective
    ]
    guessing_screen = render_guessing_screen(players_info)
    await edit_message(session, guessing_screen.textref, guessing_screen.buttons)
    return False

  # --- TOGGLE PLAYER TEAM ---
  elif data and data.startswith("g:toggle_") and session.game_substate == GuessTeamsSubstate.GUESSING:
    player_id = int(data.replace("g:toggle_", ""))
    if player_id in detective.team_guess:
      current = detective.team_guess[player_id]
      detective.team_guess[player_id] = Role.BETA.value if current == Role.ALPHA.value else Role.ALPHA.value
      # Re‑render the guessing screen with updated toggles
      players_info = [
        (p.id, p.name, detective.team_guess[p.id])
        for p in game.players if p != detective
      ]
      guessing_screen = render_guessing_screen(players_info)
      await edit_message(session, guessing_screen.textref, guessing_screen.buttons)
    return False

  # --- CONFIRM GUESS ---
  elif data == "g:confirm_guess" and session.game_substate == GuessTeamsSubstate.GUESSING:
    detective.sus_alphas = []
    detective.sus_betas = []
    for p in game.players:
      if p == detective:
        continue
      if detective.team_guess[p.id] == Role.ALPHA.value:
        detective.sus_alphas.append(p)
      else:
        detective.sus_betas.append(p)
    set_all_substates(game, GuessTeamsSubstate.RESULT, set_waited=False)
    # Result screen will be rendered in the next step

  # --- MOVE TO NEXT PHASE ---
  elif data == "g:vote_words" and session.game_substate == GuessTeamsSubstate.RESULT:
    game.state = GameState.VOTE_WORDS
    set_all_substates(game, None, set_waited=False)
    return True

  # --- RESULT SCREEN (RENDER) ---
  if session.game_substate == GuessTeamsSubstate.RESULT:
    result = game.check_detection()
    sign = '+' if result['score'] > 0 else ''
    result_text = f"{result['correct']}/{result['total']} ({sign}{result['score']}P)"
    alphas_names = [p.name for p in game.alphas]
    betas_names = [p.name for p in game.betas]
    screens = render_result_screen(result_text, alphas_names, betas_names)

    owner_session = get_session_of_owner(game=game)
    owner_session.waited = True

    # Broadcast to others (text only)
    await broadcast_message(
      game=game,
      mode="edit",
      text=screens.others.textref,
      exclude_session_ids=[owner_session.id]
    )
    # Edit owner with button
    await edit_message(owner_session, screens.special.textref, screens.special.buttons)
    return False

  # --- RENDER GUESSING SCREEN (for detective, e.g., after returning) ---
  if session.game_substate == GuessTeamsSubstate.GUESSING:
    players_info = [
      (p.id, p.name, detective.team_guess[p.id])
      for p in game.players if p != detective
    ]
    guessing_screen = render_guessing_screen(players_info)
    await edit_message(session, guessing_screen.textref, guessing_screen.buttons)
    return False

  return False