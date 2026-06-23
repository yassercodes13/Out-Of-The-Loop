#user_commands_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from flows.msg_utils import *
from flows.states import GameState
from flows.substates import SetupSubstate
from handlers.utils import *

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):  # will change this to proper start later...
  user = ensure_user(user_id = update.effective_user.id, username = update.effective_user.username)

  if context.args:
    await join_game(update, context)
    return


  keyboard = [
    [InlineKeyboardButton("Start a new game", callback_data = 's:setup_game')],
    [InlineKeyboardButton("View game rules", callback_data = 'help')], #Not applied yet, deosn't even have a prefix
  ]
  
  await context.bot.send_message(
    chat_id = update.message.chat_id,
    text = 'Welcome! Please choose an option:',
    reply_markup = InlineKeyboardMarkup(keyboard)
  )

async def start_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = ensure_user(user_id = update.effective_user.id, username = update.effective_user.username)

  keyboard = [
    [InlineKeyboardButton("Start it", callback_data = 's:setup_game')],
    [InlineKeyboardButton("don't start", callback_data = 'del_message')],
  ]

  await context.bot.send_message(
    chat_id = update.message.chat_id,
    text = 'Starting a new game ends any runinng game.',
    reply_markup = InlineKeyboardMarkup(keyboard)
  )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
  pass # will be huge later...

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, current_game = get_user_game(update)
  args = context.args

  if not args:
    text = "To join a game use:\n/join <game_code>\n\nExample:\n/join 3AB9J4"

    if current_game:
      text = (
        "⚠️ You are already in a game.\n"
        "Joining another will end your current one.\n"
        "To see your game try /game\n\n"
        + text
      )

    await context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=text
    )
    return
  
  code = args[0]
  game = get_game_by_id(code)
  if not game:
    await context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=f"Game with code {args[0]} is not found."
    )
    return
  
  if current_game == game:
    await context.bot.send_message(
      chat_id = update.effective_chat.id,
      text = "You are already in this game.\nuse /game to see it."
    )
    return
  
  if current_game:
    terminate_game(current_game)

  slots = empty_slots(game)
  msg = await context.bot.send_message(
    chat_id=update.effective_chat.id,
    text=(
      "Input players' names who will play on this phone by replying to this message\n"
      "Names should be separated by spaces or each on a line.\n"
      f"The game has room for {slots} players."
    ),
  )

  add_user_to_game(user, game)
  session = set_session(
    chat_id = update.effective_chat.id,
    message_id = msg.message_id,
    game_id = game.id,
    user_id = user.id,
    bot = context.bot,
    game_substate = SetupSubstate.INPUT_NAMES
  )

  #Notifying other sessions that another seat has been reserved
  slots = empty_slots(game)
  await broadcast_message(
    game = game, mode = "edit",
    text = (
      "Input players' names who will play on this phone by replying to this message\n"
      "Names should be separated by spaces or each on a line.\n"
      f"game has room for {slots} players"
    ),
    exclude_chat_ids = [session.chat_id],
    only_with_substate = SetupSubstate.INPUT_NAMES,
  )

async def restart_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  
  if not await check_game(update, context, game):
    return
  
  if game.state == GameState.SETUP:
    text = "Game is not started yet.\nSee it with /game or start one with /new"
    await context.bot.send_message(
      chat_id = update.effective_chat.id,
      text = text,
    )
    return
  
  if not await check_ownership(update, context, user, game):
    return
  
  game.restart_game()
  text = f'Game Restarted\nClick below to start the game.'
  buttons = [[InlineKeyboardButton("Start Game", callback_data='g:start_round')]]
  session = get_session_of_chat(update.effective_chat.id)
  
  set_all_substates(game, SetupSubstate.FINISHED)
  await broadcast_message(game = game, mode = "edit", text = "Game Restarted by owner", exclude_chat_ids = [session.chat_id])
  await edit_message(session, text, buttons)

async def resend_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  
  if not await check_game(update, context, game):
    return
  
  session = get_session_of_chat(update.effective_chat.id)
  await send_message(session, text = session.text, buttons = session.build_buttons(), parse_mode = session.parse_mode)

async def del_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.effective_message
  if update.message:
    message = update.message
  elif update.callback_query:
    message = update.callback_query.message
  await message.delete()
  
async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  
  if not await check_game(update, context, game):
    return
  
  if not await check_ownership(update, context, user, game):
    return
  
  await broadcast_message(game=game, mode="edit", text="Game was ended by owner.")
  terminate_game(game)
  return 

async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  
  if not await check_game(update, context, game):
    return
  
  if await check_ownership(update, context, user, game):
    await broadcast_message(game = game, mode = "edit", text = "Owner has leaved, so the game has ended.")
    terminate_game(game)
    return
  else:
    pass #should do something TODO

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  
  if game:
    await context.bot.send_message(
      chat_id = update.effective_chat.id,
      text = "You can't edit settings in a running game.\nTry /end to end the current game or /game to see it."
    )
    return

  new_message = await context.bot.send_message(
    chat_id = update.effective_chat.id,
    text = "Choose what you want to edit",
    reply_markup = InlineKeyboardMarkup([
      [InlineKeyboardButton("Categories", callback_data = "e:categories")],
      [InlineKeyboardButton("Modes", callback_data = "e:modes")],
      [InlineKeyboardButton("Done", callback_data = f"e:done")]
    ])
  )

  session = set_session(
    chat_id = update.effective_chat.id,
    message_id = new_message.message_id,
    game_id = None,
    user_id = update.effective_user.id,
    bot = context.bot,
  )
  
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user, game = get_user_game(update)
  args = context.args

  # No message
  if not args:
    await update.message.reply_text(
      "Usage:\n/broadcast <message>\n\nExample:\n/broadcast hurry up!"
    )
    return

  if not await check_game(update, context, game):
    return

  message_text = " ".join(args)


  # Send to all sessions in game except sender
  sender_session = get_session_of_user(user.id, user.username)
  for cid in game.chat_ids:
    session = get_session_of_chat(cid)
    if session == sender_session:
      continue

    formatted = f"{sender_session.players[0].name}: {message_text}"
    try:
      await context.bot.send_message(
        chat_id = session.chat_id,
        text = formatted
      )
    except Exception as e:
      print(f"Broadcast failed for session {session.chat_id}: {e}")

async def check_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: Game):
  if not game:
    if update.callback_query:
      await update.callback_query.answer(
        text = "You are not in a game."
      )
    else:
      await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = "You have no running game.\nTry /new to start one" 
      )
    return False
  return True

async def check_ownership(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, game: Game):
  if game.owner_id != user.id:
    await context.bot.send_message(
      chat_id = update.effective_chat.id,
      text = "You are not the owner.\nYou can leave the game using /leave"
    )
    return False
  return True

help_handler = CommandHandler('help', help)
end_handler = CommandHandler('end', end_game)
join_handler = CommandHandler('join', join_game)
resend_handler = CommandHandler('game', resend_game)
start_bot_handler = CommandHandler('start', start_bot)
reset_handler = CommandHandler('restart', restart_game)
start_new_game_handler = CommandHandler('new', start_new_game)
edit_settings_handler = CommandHandler('settings', settings)
broadcast_handler = CommandHandler(["broadcast", "bc"], broadcast)

#Spical handlers for callback queries with no prefix, these are not routed through the game router
help_callback_handler = CallbackQueryHandler(help, pattern='help')
del_message_handler = CallbackQueryHandler(del_message, pattern='del_message')

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