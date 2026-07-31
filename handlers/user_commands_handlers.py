import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from flows.choose_player import render_players_screen
from flows.utils import *
from flows.states import GameState
from flows.substates import InterruptSubstate, SetupSubstate
from handlers.utils import *
from texts import t, b, set_lang
from adapters.telegram.messaging import *
from services.game_services import remove_players

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

  if game.state != GameState.SETUP:
    await context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=t("game_already_started")
    )
    return

  if current_game:
    logger.info(f"User {user.id} left game {current_game.id} to join game {game.id}")
    await terminate_game(current_game)

  slots = empty_slots(game)
  msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=t("input_names", slots=slots))

  add_user_to_game(user, game)
  session = await set_session(
    chat_id = update.effective_chat.id,
    message_id = msg.message_id,
    game_id = game.id,
    user_id = user.id,
    bot = context.bot,
    job_queue = context.job_queue, 
    game_substate = SetupSubstate.INPUT_NAMES
  )
  session.waited = True
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

  set_all_substates(game, SetupSubstate.FINISHED, set_waited = True)
  await broadcast_message(game=game, mode="edit", text=t("restart_game_broadcast"), exclude_chat_ids=[session.chat_id])
  await edit_message(session, t("restart_game_confirm"), buttons)


async def resend_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game):
    return

  session = get_session_of_chat(update.effective_chat.id)
  if session:
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
  session: Session = await get_session_of_user(user_id = user.id, username = user.username)
  set_lang(user.lang)

  if not await check_game(update, context, game): return
  if not session:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t("not_in_a_game"))
    return

  if session.chat_id not in game.chat_ids: return

  if len(session.players) == 1:
    await remove_players(game, [p.id for p in session.players])
  else:
    session.interrupt_substate = InterruptSubstate.REMOVE_PLAYER
    await render_players_screen(game, session, session.players, all_option=True)


async def kick_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = await get_user_game(update)
  set_lang(user.lang)

  if not await check_game(update, context, game): return
  if not await check_ownership(update, context, user, game): return

  if len(game.chat_ids) < 2:
    await context.bot.send_message(chat_id = update.effective_chat.id, text = t("kick_inavailable"))
    return
  
  session: Session = await get_session_of_user(user_id = user.id, username = user.username)
  if not session or session.chat_id not in game.chat_ids:
    await update.effective_chat.send_message(text=t("not_in_a_game"))
    return

  session.interrupt_substate = InterruptSubstate.REMOVE_PLAYER
  players = [p for p in game.players if p not in session.players]
  await render_players_screen(game, session, players)


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

  await set_session(
    chat_id=update.effective_chat.id,
    message_id=new_message.message_id,
    game_id=None,
    user_id=update.effective_user.id,
    bot=context.bot,
    job_queue=context.job_queue,
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
  
  game.set_reminder(context)
  if sender_session:
    sender_session.set_reminder(context = context)
  

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
leave_game_handler       = CommandHandler('leave', leave_game)
kick_player_handler      = CommandHandler('kick', kick_player)
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
  kick_player_handler,
  leave_game_handler,
  broadcast_handler,
  edit_settings_handler,
]