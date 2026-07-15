from telegram import Update
from data.runtime import *
from data.runtime_manager import *
from texts import supported_langs

async def get_user_game(update: Update):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang = get_user_lang(update))
  game = await get_game_of_user(user=user)
  return (user, game)


def get_session_game(update: Update):
  chat_id = update.effective_chat.id
  session = get_session_of_chat(chat_id=chat_id)
  game = get_game_of_session(chat_id=chat_id)
  return (session, game)


def get_user_lang(update: Update):
  code = update.effective_user.language_code or 'en'  # language_code can be None on some Telegram accounts
  lang = code.split("-")[0]
  lang = lang if lang in supported_langs else 'en'
  return lang


def is_active(update: Update):
  chat_id = update.effective_chat.id
  active_session = get_session_of_chat(chat_id)

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


async def end_game(game: Game):
  await terminate_game(game=game)