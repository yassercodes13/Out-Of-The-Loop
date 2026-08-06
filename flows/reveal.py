from models.game import Game
from models.session import Session
from models.modes import GameMode
from flows.states import GameState
from flows.substates import RevealSubstate
from telegram import Update
from flows.utils import set_all_substates
from data.links import get_session_of_owner, get_session_by_id
from adapters.telegram.messaging import edit_message, broadcast_message
from views.reveal import (
  render_single_outsider_screen,
  render_double_outsider_screen,
  render_detective_reveal_screen,
  render_teams_reveal_screen,
)


async def handle_reveal(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:reveal" and session.game_substate is None:
    game.sessions_ready = 0
    outsiders = game.outsiders
    set_all_substates(game, RevealSubstate.CHOICE, set_waited=False)

    if len(outsiders) == 1:
      screens = render_single_outsider_screen(outsiders[0].name)
      outsider_session = get_session_by_id(outsiders[0].session_id)
      outsider_session.waited = True

      await broadcast_message(
        game=game,
        mode="edit",
        text=screens.others.textref,
        exclude_session_ids=[outsider_session.id]
      )
      await edit_message(outsider_session, screens.special.textref, screens.special.buttons)

    elif len(outsiders) == 2:
      screens = render_double_outsider_screen(outsiders[0].name)
      outsider_session = get_session_by_id(outsiders[0].session_id)
      outsider_session.waited = True

      await broadcast_message(
        game=game,
        mode="edit",
        text=screens.others.textref,
        exclude_session_ids=[outsider_session.id]
      )
      await edit_message(outsider_session, screens.special.textref, screens.special.buttons)

    elif game.mode == GameMode.TEAMS and game.detective:
      screens = render_detective_reveal_screen(game.detective.name)
      detective_session = get_session_by_id(game.detective.session_id)
      detective_session.waited = True

      await broadcast_message(
        game=game,
        mode="edit",
        text=screens.others.textref,
        exclude_session_ids=[detective_session.id]
      )
      await edit_message(detective_session, screens.special.textref, screens.special.buttons)

    elif game.mode == GameMode.TEAMS and not game.detective:
      screens = render_teams_reveal_screen(
        [p.name for p in game.alphas],
        [p.name for p in game.betas]
      )
      owner_session = get_session_of_owner(game=game)
      owner_session.waited = True

      await broadcast_message(
        game=game,
        mode="edit",
        text=screens.others.textref,
        exclude_session_ids=[owner_session.id]
      )
      await edit_message(owner_session, screens.special.textref, screens.special.buttons)

    return False

  elif session.game_substate == RevealSubstate.CHOICE:
    # Branching: set next state based on button pressed
    set_all_substates(game, None, set_waited=False)
    if data and data.startswith("g:guess_word:"):
      game.state = GameState.GUESS_WORD
    elif data == "g:guess_outsider":
      game.state = GameState.GUESS_OUTSIDER
    elif data == "g:vote_words":
      game.state = GameState.VOTE_WORDS
    elif data == "g:guess_teams":
      game.state = GameState.GUESS_TEAMS
    return True

  return False