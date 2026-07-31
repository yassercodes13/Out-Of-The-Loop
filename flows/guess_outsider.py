from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessOutsiderSubstate
from telegram import InlineKeyboardButton, Update
from flows.utils import *
from data.runtime_manager import get_session_of_owner
from texts import t, b
from adapters.telegram.messaging import *

# --- screen renderers ---

async def render_guess_outsider_screen(session: Session, game: Game):
  buttons = []
  for p in game.players:
    if p != game.outsiders[0]:
      buttons.append([InlineKeyboardButton(p.name, callback_data=f"g:guess:{p.id}")])
  
  text = t("choose_outsider")
  await edit_message(session, text, buttons)

async def render_result_screen(game: Game, is_correct: bool):
  text = t("outsider_correct") if is_correct else t("outsider_wrong", name=game.outsiders[1].name)
  buttons = [[InlineKeyboardButton(b("guess_word"), callback_data="g:guess_word:1")]]
  
  owner_session = get_session_of_owner(game=game)
  owner_session.waited = True
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
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