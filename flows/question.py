from data.modes import GameMode
from flows.states import GameState
from flows.substates import QuestionSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *

async def handle_questioning(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data

  # --- STATE TRANSITIONS ---

  if data == 'g:start_question':
    game.turn_index = 0
    set_all_substates(game, QuestionSubstate.ASK)
  
  elif data == 'g:next':
    game.turn_index += 1

  elif data == 'g:back':
    game.turn_index -= 1
    game.turn_index = max(0, game.turn_index)

  elif data == "g:start_vote":
    game.state = GameState.VOTE
    set_all_substates(game, None)
    return True
  
  elif data == "g:extra_questions":
    game.pair_players()
    game.turn_index = 0


  # --- END CONDITION ---

  if game.turn_index >= len(game.pairs):
    set_all_substates(game, QuestionSubstate.END)
    
    if game.mode == GameMode.TEAMS:
      text = "Now you are ready to vote each other."
    else:
      text = "Now you are ready to vote the outsider."
    buttons = [
      [InlineKeyboardButton("Start Voting", callback_data = "g:start_vote")],
      [InlineKeyboardButton("Extra Questions", callback_data = "g:extra_questions")], 
      [InlineKeyboardButton("Back", callback_data = "g:back")],
    ]
    
    await edit_message(session, text, buttons)
    return False
  

  # --- RENDER CURRENT STEP ---

  pair = game.pairs[game.turn_index]
  message = f'{pair[0].name} ask {pair[1].name}'

  buttons = [
    [InlineKeyboardButton("Next", callback_data = 'g:next')],
  ]

  if game.turn_index > 0:
    buttons.append([InlineKeyboardButton("Back", callback_data="g:back")])

  text = message

  await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [session.chat_id])
  await edit_message(session, text, buttons)

  return False