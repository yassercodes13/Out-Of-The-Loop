from telegram import Update
from handlers.utils import *
from flows.router import route_game
from flows.substates import SetupSubstate
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  data = query.data if query else None
  ensure_user(user_id = update.effective_user.id, username = update.effective_user.username)

  if not data or not data.startswith(("s:", "g:", "e:")):
    return

  session, game = get_session_game(update)

  is_starting_game = data == "s:setup_game"
  
  if not is_active(update) and not is_starting_game:
    await query.answer(text = "This is not Active anymore.")
    return

  await route_game(update, context, game, session)

  
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
  session, game = get_session_game(update)
  if not is_active(update):
    if game and session and session.game_substate == SetupSubstate.INPUT_NAMES:
      await update.effective_chat.send_message(text = "This is not the right message.\nTry /game to see the active game.")
    return

  await route_game(update, context, game, session)
  

callback_handler = CallbackQueryHandler(handle_callback, pattern = r"^(g:|s:|e:)")
reply_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY, handle_reply)

interaction_handlers = [
  callback_handler,
  reply_handler
]