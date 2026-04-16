from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import GuessWordSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *

async def handle_guess_word(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data and data.startswith("g:guess_word:") and session.game_substate is None:      # Only the guesser interacts with this phase (session is set in reveal phase)
    session.game_substate = GuessWordSubstate.CHOOSING
    
    parts = data.split(":")
    out_idx = int(parts[2])
    game.word_guesser = game.outsiders[out_idx]

    set_all_substates(game, GuessWordSubstate.WAITING, exclude_chat_ids = [session.chat_id])
    await broadcast_message(game = game, mode = "edit", text = f"{game.word_guesser.name} is guessing a word...", exclude_chat_ids = [session.chat_id])


    buttons = []
    for i,choice in enumerate(game.choices):
      buttons.append([InlineKeyboardButton(choice, callback_data=f"g:choice:{i}")])
    
    text=f"{game.word_guesser.name}, Try to guess the word"

    await edit_message(session, text, buttons)
  
  if session.game_substate == GuessWordSubstate.CHOOSING and data and data.startswith("g:choice:"):
    set_all_substates(game, GuessWordSubstate.RESULT)

    word_idx = int(query.data.split(":")[2])
    word = game.choices[word_idx]
    result = game.check_word(word)

    result_message = f"{word} is Correct!" if result else f'{word} is Wrong! The word was "{game.word}"'
    text = f"{result_message}\n\nNow Let's see results"
    buttons = [[InlineKeyboardButton("See Results", callback_data = "g:results")]]
    
    owner_session = get_session_of_owner(game=game)
    
    await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [owner_session.chat_id])
    await edit_message(owner_session, text, buttons)
    
    game.state = GameState.RESULTS
    set_all_substates(game, None)
    
    return False
