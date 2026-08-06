from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessWordSubstate
from telegram import Update
from flows.utils import set_all_substates
from data.links import get_session_of_owner, get_session_by_id
from adapters.telegram.messaging import broadcast_message, edit_message
from views.guess_word import (
  render_waiting_screen,
  render_choose_word_screen,
  render_guess_result_screen,
)

async def handle_guess_word(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data and data.startswith("g:guess_word:") and session.game_substate is None:
    session.game_substate = GuessWordSubstate.CHOOSING
    session.waited = True

    parts = data.split(":")
    out_idx = int(parts[2])
    game.word_guesser = game.outsiders[out_idx]

    set_all_substates(game, GuessWordSubstate.WAITING, exclude_session_ids=[session.id])

    waiting_screen = render_waiting_screen(game.word_guesser.name)
    await broadcast_message(
      game=game,
      mode="edit",
      text=waiting_screen.textref,
      exclude_session_ids=[session.id]
    )

    choose_screen = render_choose_word_screen(game.word_guesser.name, game.choices)
    await edit_message(session, choose_screen.textref, choose_screen.buttons)

  if session.game_substate == GuessWordSubstate.CHOOSING and data and data.startswith("g:choice:"):
    set_all_substates(game, GuessWordSubstate.RESULT)

    word_idx = int(data.split(":")[2])
    word = game.choices[word_idx]
    result = game.check_word(word)
    get_session_by_id(game.word_guesser.session_id).waited = False

    screens = render_guess_result_screen(word, result, game.word)

    await broadcast_message(
      game=game,
      mode="edit",
      text=screens.others.textref,
      exclude_session_ids=[game.owner_session_id]
    )

    owner_session = get_session_of_owner(game=game)
    await edit_message(owner_session, screens.special.textref, screens.special.buttons)

  if session.game_substate == GuessWordSubstate.RESULT and data and data.startswith("g:round_results"):
    game.state = GameState.RESULTS
    set_all_substates(game, None, set_waited=False)
    return True