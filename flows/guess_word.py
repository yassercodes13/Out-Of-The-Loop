from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessWordSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *
from data.runtime_manager import get_session_of_owner
from texts import t, b

# --- screen renderers ---

async def render_waiting_broadcast(session: Session, game: Game):
  text = t("is_guessing", name=game.word_guesser.name)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[session.chat_id])

async def render_choose_word_screen(session: Session, game: Game):
  buttons = []
  for i, choice in enumerate(game.choices):
    buttons.append([InlineKeyboardButton(choice, callback_data=f"g:choice:{i}")])
  
  text = t("try_guess", name=game.word_guesser.name)
  await edit_message(session, text, buttons)

async def render_guess_result_screen(game: Game, word: str, result: bool):
  if result:
    result_message = t("word_correct", word=word)
  else:
    result_message = t("word_wrong", word=word, correct_word=game.word)
  
  text = t("let's_see_results", result_message=result_message)
  buttons = [[InlineKeyboardButton(b("see_results"), callback_data="g:round_results")]]
  
  owner_session = get_session_of_owner(game=game)
  
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
  await edit_message(owner_session, text, buttons)

# --- dispatch ---

async def handle_guess_word(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data and data.startswith("g:guess_word:") and session.game_substate is None:
    session.game_substate = GuessWordSubstate.CHOOSING
    
    parts = data.split(":")
    out_idx = int(parts[2])
    game.word_guesser = game.outsiders[out_idx]

    set_all_substates(game, GuessWordSubstate.WAITING, exclude_chat_ids=[session.chat_id])
    
    await render_waiting_broadcast(session, game)
    await render_choose_word_screen(session, game)
  
  if session.game_substate == GuessWordSubstate.CHOOSING and data and data.startswith("g:choice:"):
    set_all_substates(game, GuessWordSubstate.RESULT)

    word_idx = int(query.data.split(":")[2])
    word = game.choices[word_idx]
    result = game.check_word(word)

    await render_guess_result_screen(game, word, result)
    
    game.state = GameState.RESULTS
    set_all_substates(game, None)
    
    return False