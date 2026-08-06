from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessOutsiderSubstate
from telegram import Update
from flows.utils import set_all_substates
from data.links import get_session_of_owner
from adapters.telegram.messaging import edit_message, broadcast_message
from views.guess_outsider import render_guess_outsider_screen, render_result_screen
  
async def handle_guess_outsider(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:guess_outsider" and session.game_substate is None:
    session.game_substate = GuessOutsiderSubstate.CHOOSING
    session.waited = True

    screen = render_guess_outsider_screen(game)
    await edit_message(session, screen.textref, screen.buttons)
    return False

  if session.game_substate == GuessOutsiderSubstate.CHOOSING and data and data.startswith("g:guess:"):
    guessed_id = int(data.split(":")[2])    
    is_correct = game.check_suspect(guessed_id)
    
    session.waited = False
    outsider_name = game.outsiders[1].name

    screen = render_result_screen(is_correct, outsider_name)
    owner_session = get_session_of_owner(game=game)
    owner_session.waited = True

    await broadcast_message(game = game, mode="edit", text = screen.textref, exclude_session_ids = [owner_session.id])
    await edit_message(owner_session, screen.textref, screen.buttons)
    
    game.state = GameState.GUESS_WORD
    set_all_substates(game, None)
    return False