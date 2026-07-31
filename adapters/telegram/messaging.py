import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message
from data.runtime_manager import *
from flows.substates import AnySubstate
from .retry import retry_async
from .limits import check_buttons, check_text_length
from telegram.error import BadRequest, Forbidden, ChatMigrated
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from models.game import Game
  from models.session import Session

# --- For Main Screen messages ---

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

  out = await retry_async(
    lambda: session.bot.edit_message_text(
      chat_id = session.chat_id, 
      message_id = session.message_id, 
      text = text, 
      reply_markup = markup, 
      parse_mode = parse_mode
      ), 
      f"Edit message (Chat ID: {session.chat_id})"
    )
  
  if isinstance(out, Message):
    session.set_ui(text = text, raw_markup = raw_markup)

  return True


async def send_message(session: Session, text: str, buttons: list[list[InlineKeyboardButton]] = None, old_message: Message = None, delete_old_message: bool = False, parse_mode: str = None):
  if old_message and delete_old_message:
    await retry_async(lambda: old_message.delete(), f"Delete old message (Chat ID: {session.chat_id})")

  check_text_length(text, label=f"Message for Chat ID: {session.chat_id}")
  if buttons:
    check_buttons(buttons, chat_id = session.chat_id)

  markup = InlineKeyboardMarkup(buttons) if buttons else None

  sent_msg = await retry_async(
    lambda: session.bot.send_message(
      chat_id = session.chat_id,
      text = text,
      reply_markup = markup,
      parse_mode = parse_mode),
      f"Send message (Chat ID: {session.chat_id})"
    )
  
  if isinstance(sent_msg, Message):
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
  sessions = get_all_sessions(game = game, excluded = exclude_chat_ids)

  if only_with_substate:
    sessions = [s for s in sessions if only_with_substate == s.game_substate]

  for session in sessions:
    if mode == "edit":
      tasks.append(edit_message(session = session, text = text, buttons = buttons, parse_mode = parse_mode))
    elif mode == "send":
      tasks.append(send_message(session = session, text = text, buttons = buttons, parse_mode = parse_mode))

  if tasks:
    await asyncio.gather(*tasks, return_exceptions=True)
  

# --- For messages that don't change Sessions States ---

async def send_popup_message(session: Session = None, text: str = "", buttons: list[list[InlineKeyboardButton]] = None, target: Session | Game = None) -> Message:

  if not session: return
  chat_id = session.chat_id
  bot = session.bot

  #Checking Limits
  check_text_length(text, label = f"Popup message (Chat ID: {chat_id})")
  if buttons:
    check_buttons(buttons, chat_id = chat_id)

  #Actually Sending
  markup = InlineKeyboardMarkup(buttons) if buttons else None
  msg = await retry_async(
    lambda: bot.send_message(chat_id = chat_id, text = text, reply_markup = markup),
    f"Send stateless message (Chat ID: {chat_id})"
  )

  #Saving the new popup
  if target and isinstance(msg, Message):
    if target.popup_message_id:
      await delete_popup(target)
    target.popup_message_id = msg.id
    
  return msg


async def delete_popup(target: Session | Game):
  """Deletes the popup message stored on a Session or Game object."""
  if not target or not target.popup_message_id:
    return

  msg_id = target.popup_message_id
  target.popup_message_id = None

  if isinstance(target, Session):
    bot = target.bot
    chat_id = target.chat_id
  else:  # Game
    owner_session = get_session_of_owner(game=target)
    if not owner_session: return
    bot = owner_session.bot
    chat_id = owner_session.chat_id

  # Use retry_async for the actual network deletion
  try:
    await retry_async(
      lambda: bot.delete_message(chat_id=chat_id, message_id=msg_id),
      f"Delete popup ({target.__class__}) from {chat_id}"
    )
  except (BadRequest, Forbidden, ChatMigrated):
    pass 
    #It's okay, id is already cleaned
  

# --- For non-interactive messages ---

async def send_info_message(bot: Bot, chat_id: int, text: str):

  """Sends a simple, non-tracked, non-interactive message with full checks."""

  check_text_length(text, label = f"Info message (Chat ID: {chat_id})")
  msg = await retry_async(
    lambda: bot.send_message(chat_id = chat_id, text = text),
    f"Send info message (Chat ID: {chat_id})"
  )
  return msg