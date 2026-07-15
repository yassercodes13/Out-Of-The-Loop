import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from flows.utils import *
from flows.states import GameState
from flows.substates import SetupSubstate
from handlers.utils import *
from texts import t, b, set_lang
from adapters.telegram.messaging import *

logger = logging.getLogger(__name__)


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  set_lang(user.lang)
  logger.info(f"User {user.id} ({user.username}) started bot")

  if context.args:
    await join_game(update, context)
    return

  keyboard = [
    [InlineKeyboardButton(b("start_game"), callback_data='s:setup_game')],
    [InlineKeyboardButton(b("view_game_rules"), callback_data='help')],
  ]

  await context.bot.send_message(
    chat_id=update.message.chat_id,
    text=t("welcome"),
    reply_markup=InlineKeyboardMarkup(keyboard)
  )


async def start_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  set_lang(user.lang)

  keyboard = [
    [InlineKeyboardButton(b("start_it"), callback_data='s:setup_game')],
    [InlineKeyboardButton(b("dont_start"), callback_data='del_message')],
  ]

  await context.bot.send_message(
    chat_id=update.message.chat_id,
    text=t("starting_new_game_warning"),
    reply_markup=InlineKeyboardMarkup(keyboard)
  )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  pass  # will be huge later...


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, current_game = await get_user_game(update)
  set_lang(user.lang)
  args = context.args

  if not args:
    text = t("join_usage")
    if current_game:
      text = t("already_in_game_join_warning") + text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    return

  code = args[0]
  game = get_game_by_id(code)
  if not game:
    logger.warning(f"User {user.id} tried to join nonexistent game {code}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("game_not_found", code=code))
    return

  if current_game == game:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("already_in_this_game"))
    return

  if current_game:
    logger.info(f"User {user.id} left game {current_game.id} to join game {game.id}")
    await terminate_game(current_game)

  slots = empty_slots(game)
  msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=t("input_names", slots=slots))

  add_user_to_game(user, game)
  session = set_session(
    chat_id=update.effective_chat.id,
    message_id=msg.message_id,
    game_id=game.id,
    user_id=user.id,
    bot=context.bot,
    game_substate=SetupSubstate.INPUT_NAMES
  )
  logger.info(f"User {user.id} joined game {game.id}")

  slots = empty_slots(game)
  await broadcast_message(
    game=game, mode="edit",
    text=t("input_names", slots=slots),
    exclude_chat_ids=[session.chat_id],
    only_with_substate=SetupSubstate.INPUT_NAMES,
  )


async def restart_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game):
    return

  if game.state == GameState.SETUP:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("game_not_started_yet"))
    return

  if not await check_ownership(update, context, user, game):
    return

  logger.info(f"Game {game.id} restarted by owner {user.id}")
  game.restart_game()
  buttons = [[InlineKeyboardButton(b("start_game"), callback_data='g:start_round')]]
  session = get_session_of_chat(update.effective_chat.id)

  set_all_substates(game, SetupSubstate.FINISHED)
  await broadcast_message(game=game, mode="edit", text=t("restart_game_broadcast"), exclude_chat_ids=[session.chat_id])
  await edit_message(session, t("restart_game_confirm"), buttons)


async def resend_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game):
    return

  session = get_session_of_chat(update.effective_chat.id)
  await send_message(session, text=session.text, buttons=session.build_buttons(), parse_mode=session.parse_mode)


async def del_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.effective_message
  if update.message:
    message = update.message
  elif update.callback_query:
    message = update.callback_query.message
  await message.delete()


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game):
    return

  if not await check_ownership(update, context, user, game):
    return

  logger.info(f"Game {game.id} ended by owner {user.id}")
  await broadcast_message(game=game, mode="edit", text=t("game_ended_by_owner"))
  await terminate_game(game)


async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game):
    return

  if await check_ownership(update, context, user, game):
    logger.info(f"Game {game.id} ended — owner {user.id} left")
    await broadcast_message(game=game, mode="edit", text=t("owner_left_game"))
    await terminate_game(game)
    return
  else:
    pass  # should do something TODO


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if game:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("cant_edit_in_game"))
    return

  new_message = await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=t("choose_edit"),
    reply_markup=InlineKeyboardMarkup([
      [InlineKeyboardButton(b("categories"), callback_data="e:categories")],
      [InlineKeyboardButton(b("modes"), callback_data="e:modes")],
      [InlineKeyboardButton(b("language"), callback_data="e:language")],
      [InlineKeyboardButton(b("done"), callback_data="e:done")],
    ])
  )

  set_session(
    chat_id=update.effective_chat.id,
    message_id=new_message.message_id,
    game_id=None,
    user_id=update.effective_user.id,
    bot=context.bot,
  )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)
  args = context.args

  if not args:
    await update.message.reply_text(t("broadcast_usage"))
    return

  if not await check_game(update, context, game):
    return

  message_text = " ".join(args)
  sender_session = await get_session_of_user(user.id, user.username)
  for cid in game.chat_ids:
    session = get_session_of_chat(cid)
    if session == sender_session:
      continue
    formatted = f"{sender_session.players[0].name}: {message_text}"
    try:
      await context.bot.send_message(chat_id=session.chat_id, text=formatted)
    except Exception as e:
      logger.error(f"Broadcast failed | game: {game.id} | target chat: {session.chat_id} | error: {e}")


async def check_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: Game):
  if not game:
    if update.callback_query:
      await update.callback_query.answer(text=t("not_in_a_game"))
    else:
      await context.bot.send_message(chat_id=update.effective_chat.id, text=t("no_running_game"))
    return False
  return True


async def check_ownership(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, game: Game):
  if game.owner_id != user.id:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("not_owner"))
    return False
  return True


help_handler             = CommandHandler('help', help)
end_handler              = CommandHandler('end', end_game)
join_handler             = CommandHandler('join', join_game)
resend_handler           = CommandHandler('game', resend_game)
start_bot_handler        = CommandHandler('start', start_bot)
reset_handler            = CommandHandler('restart', restart_game)
start_new_game_handler   = CommandHandler('new', start_new_game)
edit_settings_handler    = CommandHandler('settings', settings)
broadcast_handler        = CommandHandler(["broadcast", "bc"], broadcast)
help_callback_handler    = CallbackQueryHandler(help, pattern='help')
del_message_handler      = CallbackQueryHandler(del_message, pattern='del_message')

user_commands_handlers = [
  start_bot_handler,
  start_new_game_handler,
  help_handler,
  join_handler,
  reset_handler,
  resend_handler,
  end_handler,
  help_callback_handler,
  del_message_handler,
  broadcast_handler,
  edit_settings_handler,
]