from telegram import Update
from data.runtime import *
from data.links import get_game_of_user, get_session_by_id, get_game_of_session
from data.users import get_user_by_id
from texts import supported_langs

def get_session_game(update: Update):
  session = get_session_by_id(id = update.effective_chat.id)
  game = get_game_of_session(session_id = update.effective_chat.id)
  return (session, game)

def get_user_lang(update: Update):
  code = update.effective_user.language_code or 'en'  # language_code can be None on some Telegram accounts
  lang = code.split("-")[0]
  lang = lang if lang in supported_langs else 'en'
  return lang

def is_active(update: Update):
  chat_id = update.effective_chat.id
  active_session = get_session_by_id(id = chat_id)

  if not active_session:
    return False

  message_id = None

  if update.message and update.message.reply_to_message:
    message_id = update.message.reply_to_message.message_id
  elif update.callback_query:
    message_id = update.callback_query.message.message_id

  if not message_id:
    return False

  return active_session.message_id == message_id