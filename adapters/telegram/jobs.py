from telegram.ext import ContextTypes
from config import TIME_BEFORE_GAME_TERMINATION, TIME_BEFORE_SESSION_TERMINATION
from data.links import get_session_of_owner, get_game_by_id
from services.lifecycle_services import terminate_game, terminate_session, remove_players
from flows.states import GameState
from flows.utils import empty_slots
from adapters.telegram.messaging import broadcast_message, delete_popup, send_popup_message
from texts.refs import TextRef, Button

async def reminder_callback(context: ContextTypes.DEFAULT_TYPE):
  from data.sessions import get_session_by_id
  
  chat_id = context.job.chat_id
  session = get_session_by_id(chat_id)
  if not session: return
  
  session.reminder = None  # this job is running now, it's not "pending" anymore

  if not session.waited: return
  
  text = TextRef("still_alive")
  buttons = [
    [Button(TextRef("yes"), "i:session_alive")],
  ]
  await send_popup_message(session = session, text = text, buttons = buttons, target = session)

  session.reminder = context.job_queue.run_once(
    callback = alive_check_callback,
    chat_id = chat_id,
    when = TIME_BEFORE_SESSION_TERMINATION,
  )


async def alive_check_callback(context: ContextTypes.DEFAULT_TYPE):
  from data.sessions import get_session_by_id
  
  chat_id = context.job.chat_id
  session = get_session_by_id(chat_id)
  if not session:
    return
  session.reminder = None

  game = get_game_by_id(session.game_id)
  if not game:
    return

  if game.state == GameState.SETUP:
    await delete_popup(session)

    if session.user_id == game.owner_id:
      await terminate_game(game)
    else:
      await terminate_session(session.id)
      slots = empty_slots(game)
      await broadcast_message(game = game, mode = "edit", text = TextRef("input_names", {"slots": slots}))
    return

  players_ids = [p.id for p in session.players]
  await remove_players(game, players_ids)


async def game_reminder_callback(context: ContextTypes.DEFAULT_TYPE):
  from data.sessions import get_session_by_id

  chat_id = context.job.chat_id

  session = get_session_by_id(chat_id)
  if not session: return

  game = get_game_by_id(session.game_id)
  if not game: return

  game.reminder = None
  text = TextRef("still_running")
  buttons = [
    [Button(TextRef("yes"), "i:game_running")],
  ]

  if game.owner_session_id is None:
    await terminate_game(game)
    return
  owner_session = get_session_of_owner(game)

  await send_popup_message(session = owner_session, text = text, buttons = buttons, target = game)

  game.reminder = context.job_queue.run_once(
    callback = game_running_check_callback,
    chat_id = game.owner_session_id,
    when = TIME_BEFORE_GAME_TERMINATION
  )

async def game_running_check_callback(context: ContextTypes.DEFAULT_TYPE):
  from data.sessions import get_session_by_id
  chat_id = context.job.chat_id
  session = get_session_by_id(chat_id)
  if not session: return
  game = get_game_by_id(session.game_id)
  if not game: return

  await terminate_game(game)
  return