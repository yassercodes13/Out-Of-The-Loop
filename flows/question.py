from data.modes import GameMode
from flows.states import GameState
from flows.substates import QuestionSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *
from texts import t, b

# --- screen renderers ---

async def render_end_questions_screen(session: Session, game: Game):
  if game.mode == GameMode.TEAMS:
    text = t("ready_vote_teams")
  else:
    text = t("ready_vote_outsider")
    
  buttons = [
    [InlineKeyboardButton(b("start_voting"), callback_data="g:start_vote")],
    [InlineKeyboardButton(b("extra_questions"), callback_data="g:extra_questions")], 
    [InlineKeyboardButton(b("back"), callback_data="g:back")],
  ]
  
  await edit_message(session, text, buttons)

async def render_ask_question_screen(session: Session, game: Game):
  pair = game.pairs[game.turn_index]
  text = t("ask_question", asker=pair[0].name, answerer=pair[1].name)

  buttons = [
    [InlineKeyboardButton(b("next"), callback_data='g:next')],
  ]

  if game.turn_index > 0:
    buttons.append([InlineKeyboardButton(b("back"), callback_data="g:back")])

  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[session.chat_id])
  await edit_message(session, text, buttons)

# --- dispatch ---

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
    await render_end_questions_screen(session, game)
    return False
  
  # --- RENDER CURRENT STEP ---

  await render_ask_question_screen(session, game)
  return False