import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message
from data.runtime_manager import *
from models.session import Session
from models.game import Game
from flows.substates import AnySubstate
from .retry import retry_async
from .limits import check_buttons, check_text_length, check_callback_data

logger = logging.getLogger(__name__)


async def edit_message(session: Session, text: str, buttons: list[list[InlineKeyboardButton]] = None, parse_mode: str = None):
  raw_markup = []
  if buttons:
    for r in buttons:
      row = []
      for btn in r:
        row.append((btn.text, btn.callback_data))
      raw_markup.append(row)

  if session.text == text and session.raw_markup == raw_markup:
    return False
  
  check_text_length(text, label=f"Message for Chat ID: {session.chat_id}")
  if buttons:
    check_buttons(buttons, chat_id = session.chat_id)

  markup = InlineKeyboardMarkup(buttons) if buttons else None

  await retry_async(lambda: session.bot.edit_message_text(chat_id = session.chat_id, message_id = session.message_id, text = text, reply_markup = markup, parse_mode = parse_mode), f"Edit message (Chat ID: {session.chat_id})")
  session.set_ui(text=text, raw_markup=raw_markup)
  return True


async def send_message(session: Session, text: str, buttons: list[list[InlineKeyboardButton]] = None, old_message: Message = None, delete_old_message: bool = False, parse_mode: str = None):
  if old_message and delete_old_message:
    await retry_async(lambda: old_message.delete(), f"Delete old message (Chat ID: {session.chat_id})")

  check_text_length(text, label=f"Message for Chat ID: {session.chat_id}")
  if buttons:
    check_buttons(buttons, chat_id = session.chat_id)

  markup = InlineKeyboardMarkup(buttons) if buttons else None

  sent_msg = await retry_async(lambda: session.bot.send_message(chat_id = session.chat_id, text = text, reply_markup = markup, parse_mode = parse_mode), f"Send message (Chat ID: {session.chat_id})")
  session.message_id = sent_msg.message_id
  session.set_ui(text = text, buttons = buttons)
  return True


# TODO: Needs logging and handling edge cases. 
async def broadcast_message(game: Game, mode: str, text: str, buttons: list[list[InlineKeyboardButton]] = None, parse_mode: str = None, exclude_chat_ids: list[int] = None, only_with_substate: AnySubstate = None):
  exclude_chat_ids = exclude_chat_ids or []

  if mode not in ["edit", "send"]:
    logger.warning(f"Invalid broadcasting mode: {mode}")
    return

  tasks = []
  sessions = get_all_sessions(game=game, excluded=exclude_chat_ids)

  if only_with_substate:
    sessions = [s for s in sessions if only_with_substate == s.game_substate]

  for session in sessions:
    if mode == "edit":
      tasks.append(edit_message(session=session, text=text, buttons=buttons, parse_mode=parse_mode))
    elif mode == "send":
      tasks.append(send_message(session=session, text=text, buttons=buttons, parse_mode=parse_mode))

  if tasks:
    await asyncio.gather(*tasks, return_exceptions=True)
  