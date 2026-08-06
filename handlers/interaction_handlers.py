from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from adapters.telegram.messaging import send_info_message
from handlers.utils import get_session_game, get_user_lang, is_active
from flows.router import route_game
from data.users import ensure_user
from views.common import render_not_active_screen


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  data = query.data if query else None

  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))

  if not data or not data.startswith(("s:", "g:", "e:", "i:")):
    return

  session, game = get_session_game(update)
  if session:
    session.set_reminder(context = context)
  if game:
    game.set_reminder(context = context)

  is_starting_game = (data == "s:setup_game")
  is_interrupting = session and ((session.interrupt_substate is not None) or (data and data.startswith("i:")))

  if not is_active(update) and not is_starting_game and not is_interrupting:
    await query.answer()
    screen = render_not_active_screen()
    await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = screen.textref,
      lang = user.lang
    )
    return

  await route_game(update, context, game, session, user)


async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))

  session, game = get_session_game(update)
  if session:
    session.set_reminder(context = context)
  if game:
    game.set_reminder(context = context)

  if not is_active(update):
    if game and session:
      screen = render_not_active_screen()
      await send_info_message(
        context.bot,
        update.effective_chat.id,
        screen.textref,
        lang = user.lang
      )
    return

  await route_game(update, context, game, session, user)


callback_handler = CallbackQueryHandler(handle_callback, pattern=r"^(g:|s:|e:|i:)")
reply_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY, handle_reply)

interaction_handlers = [
  callback_handler,
  reply_handler,
]