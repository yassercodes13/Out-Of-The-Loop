from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.utils import *
from flows.router import route_game
from texts import t, set_lang


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  data = query.data if query else None

  user = ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  set_lang(user.lang)

  if not data or not data.startswith(("s:", "g:", "e:")):
    return

  session, game = get_session_game(update)

  is_starting_game = (data == "s:setup_game")

  if not is_active(update) and not is_starting_game:
    await query.answer(text=t("not_active"))
    return

  await route_game(update, context, game, session)


async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  set_lang(user.lang)

  session, game = get_session_game(update)

  if not is_active(update):
    if game and session:
      await update.effective_chat.send_message(text=t("wrong_message"))
    return

  await route_game(update, context, game, session)


callback_handler = CallbackQueryHandler(handle_callback, pattern=r"^(g:|s:|e:)")
reply_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY, handle_reply)

interaction_handlers = [
  callback_handler,
  reply_handler,
]