from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessOutsiderSubstate
from telegram import Update
from flows.utils import *
from data.links import get_session_of_owner
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_guess_outsider_screen(session: Session, game: Game):
  buttons = []
  for p in game.players:
    if p != game.outsiders[0]:
      buttons.append([Button(TextRef("text", {"text": p.name}), f"g:guess:{p.id}")])
  
  text = TextRef("choose_outsider")
  await edit_message(session, text, buttons)

async def render_result_screen(game: Game, is_correct: bool):
  text = TextRef("outsider_correct") if is_correct else TextRef("outsider_wrong", {"name": game.outsiders[1].name})
  buttons = [[Button(TextRef("guess_word"), "g:guess_word:1")]]
  
  owner_session = get_session_of_owner(game = game)
  owner_session.waited = True
  await broadcast_message(game = game, mode="edit", text = text, exclude_session_ids = [owner_session.id])
  await edit_message(owner_session, text, buttons)

# --- dispatch ---

async def handle_guess_outsider(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:guess_outsider" and session.game_substate is None:
    session.game_substate = GuessOutsiderSubstate.CHOOSING
    session.waited = True

    await render_guess_outsider_screen(session, game)
    return False

  if session.game_substate == GuessOutsiderSubstate.CHOOSING and data and data.startswith("g:guess:"):
    guessed_id = int(data.split(":")[2])    
    is_correct = game.check_suspect(guessed_id)
    
    session.waited = False
    await render_result_screen(game, is_correct)
    
    game.state = GameState.GUESS_WORD
    set_all_substates(game, None)
    return False