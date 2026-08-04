import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from flows.choose_player import render_players_screen
from flows.utils import empty_slots, set_all_substates
from models.user import User
from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import InterruptSubstate, SetupSubstate
from handlers.utils import get_user_lang
from adapters.telegram.messaging import broadcast_message, edit_message, send_message, send_info_message
from texts.refs import TextRef, Button
from data.links import link_user_and_game, get_game_by_id, get_session_of_user, get_game_of_user, get_session_by_id
from services.lifecycle_services import set_session, terminate_game, remove_players
from data.users import ensure_user

logger = logging.getLogger(__name__)


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  logger.info(f"User {user.id} ({user.username}) started bot")

  if context.args:
    await join_game(update, context)
    return

  buttons = [
    [Button(TextRef("start_game"), 's:setup_game')],
    [Button(TextRef("view_game_rules"), 'help')],
  ]

  await send_info_message(
    bot = context.bot,
    chat_id = update.message.chat_id,
    text = TextRef("welcome"),
    buttons = buttons,
    lang = user.lang
  )


async def start_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))

  buttons = [
    [Button(TextRef("start_it"), 's:setup_game')],
    [Button(TextRef("dont_start"), 'del_message')],
  ]

  await send_info_message(
    bot = context.bot,
    chat_id = update.message.chat_id,
    text = TextRef("starting_new_game_warning"),
    buttons = buttons,
    lang = user.lang
  )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  pass


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  current_game = await get_game_of_user(user.id)
  args = context.args

  if not args:
    text = [TextRef("join_usage")]
    if current_game:
      text = [TextRef("already_in_game_join_warning")] + text
    await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = text,
      lang = user.lang
    )
    return

  code = args[0]
  game = get_game_by_id(code)
  if not game:
    logger.warning(f"User {user.id} tried to join nonexistent game {code}")
    await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = TextRef("game_not_found", {"code":code}),
      lang = user.lang
    )
    return

  if current_game == game:
    await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = TextRef("already_in_this_game"),
      lang = user.lang
    )
    return

  if game.state != GameState.SETUP:
    await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = TextRef("game_already_started"),
      lang = user.lang
    )
    return

  if current_game:
    session = await get_session_of_user(user.id)
    await remove_players(game = current_game, player_ids = [p.id for p in session.players])

  slots = empty_slots(game)
  msg = await send_info_message(
    bot = context.bot,
    chat_id = update.effective_chat.id,
    text = TextRef("input_names", {"slots" : slots}),
    lang = user.lang
  )

  link_user_and_game(user, game)
  session = await set_session(
    id = update.effective_chat.id,
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
    game = game, mode="edit",
    text = TextRef("input_names", {"slots" : slots}),
    exclude_session_ids = [session.id],
    only_with_substate = SetupSubstate.INPUT_NAMES,
  )


async def restart_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)

  if not await check_game(update, context, game, user):
    return

  if game.state == GameState.SETUP:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("game_not_started_yet"),
      lang = user.lang
    )
    return

  if not await check_ownership(update, context, user, game):
    return

  logger.info(f"Game {game.id} restarted by owner {user.id}")
  game.restart_game()
  buttons = [[Button(TextRef("start_game"), 'g:start_round')]]
  session = get_session_by_id(update.effective_chat.id)

  set_all_substates(game, SetupSubstate.FINISHED, set_waited = True)
  await broadcast_message(game=game, mode="edit", text=TextRef("restart_game_broadcast"), exclude_session_ids=[session.id])
  await edit_message(session, TextRef("restart_game_confirm"), buttons)


async def resend_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)

  if not await check_game(update, context, game, user):
    return

  session = get_session_by_id(update.effective_chat.id)
  if session:
    await send_message(session, text = session.text, buttons = session.raw_markup, parse_mode=session.parse_mode)


async def del_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.effective_message
  if update.message:
    message = update.message
  elif update.callback_query:
    message = update.callback_query.message
  await message.delete()


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)

  if not await check_game(update, context, game, user):
    return

  if not await check_ownership(update, context, user, game):
    return

  logger.info(f"Game {game.id} ended by owner {user.id}")
  await broadcast_message(game=game, mode="edit", text=TextRef("game_ended_by_owner"))
  await terminate_game(game)


async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)
  session: Session = await get_session_of_user(user_id = user.id)

  if not await check_game(update, context, game, user): return
  if not session:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("not_in_a_game"),
      lang = user.lang
    )
    return

  if session.id not in game.session_ids: return

  if len(session.players) == 1:
    await remove_players(game, [p.id for p in session.players])
  else:
    session.interrupt_substate = InterruptSubstate.REMOVE_PLAYER
    await render_players_screen(game, session, session.players, all_option=True)


async def kick_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)

  if not await check_game(update, context, game, user): return
  if not await check_ownership(update, context, user, game): return

  if len(game.session_ids) < 2:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("kick_inavailable"),
      lang = user.lang
    )
    return
  
  session: Session = await get_session_of_user(user_id = user.id)
  if not session or session.id not in game.session_ids:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("not_in_a_game"),
      lang = user.lang
    )
    return

  session.interrupt_substate = InterruptSubstate.REMOVE_PLAYER
  players = [p for p in game.players if p not in session.players]
  await render_players_screen(game, session, players)


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)

  if game:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("cant_edit_in_game"),
      lang = user.lang
    )
    return

  new_message = await send_info_message(
    bot = context.bot,
    chat_id = update.effective_chat.id,
    text = TextRef("choose_edit"),
    buttons = [
      [Button(TextRef("categories"), "e:categories")],
      [Button(TextRef("modes"), "e:modes")],
      [Button(TextRef("language"), "e:language")],
      [Button(TextRef("done"), "e:done")],
    ],
    lang = user.lang,
  )

  await set_session(
    id = update.effective_chat.id,
    game_id = None,
    message_id = new_message.message_id,
    user_id = update.effective_user.id,
    bot = context.bot,
    job_queue = context.job_queue,
  )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = await ensure_user(user_id=update.effective_user.id, username=update.effective_user.username, lang=get_user_lang(update))
  game = await get_game_of_user(user.id)
  args = context.args

  if not args:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("broadcast_usage"),
      lang = user.lang
    )
    return

  if not await check_game(update, context, game, user):
    return

  message_text = " ".join(args)
  sender_session = await get_session_of_user(user.id)
  
  game.set_reminder(context)
  if sender_session:
    sender_session.set_reminder(context = context)
  

  for sid in game.session_ids:
    session = get_session_by_id(sid)
    if session == sender_session:
      continue
    formatted = f"{sender_session.players[0].name}: {message_text}"
    try:
      await send_info_message(
        context.bot,
        session.id,
        TextRef("text", {"text": formatted}),
        lang = user.lang
      )
    except Exception as e:
      logger.error(f"Broadcast failed | game: {game.id} | target chat: {session.id} | error: {e}")


async def check_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: Game, user: User):
  if not game:
    if update.callback_query:
      await update.callback_query.answer()
      await send_info_message(
      bot = context.bot,
      chat_id = update.effective_chat.id,
      text = TextRef("not_in_a_game"),
      lang = user.lang
    )
    else:
      await send_info_message(
        bot = context.bot,
        chat_id = update.effective_chat.id,
        text = TextRef("no_running_game"),
        lang = user.lang
      )
    return False
  return True


async def check_ownership(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, game: Game):
  if game.owner_id != user.id:
    await send_info_message(
      bot = context.bot,
      chat_id=update.effective_chat.id,
      text = TextRef("not_owner"),
      lang = user.lang
    )
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