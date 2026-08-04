import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import BOT_USERNAME
from data.links import get_user_by_id, get_session_by_id, get_session_of_owner, get_all_sessions
from flows.substates import AnySubstate
from .retry import retry_async
from .limits import check_callback_data, check_text_length
from telegram.error import BadRequest, Forbidden, ChatMigrated
from typing import TYPE_CHECKING
from texts import t, b
from texts.refs import TextRef, Button
from models.user import User
from models.session import Session
from models.game import Game

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from models.game import Game
  from models.session import Session

def textify(text: TextRef | list[TextRef], lang = "en", use_b : bool = False):
  if isinstance(text, TextRef):
    key, kwargs = text
    if kwargs is None: kwargs = {}
    resolved = {
      k: textify(v, lang) if isinstance(v, (TextRef, tuple, list)) else v
      for k, v in kwargs.items()
    }
    if use_b:
      text = b(key, lang, **resolved)
    else:
      text = t(key, lang, **resolved)

  elif isinstance(text, list):
    text = [textify(item, lang, use_b) for item in text]
    text = "".join(text)

  return text

def build_buttons(raw_markup: list[list[Button]], chat_id: str, lang = "en"):
  buttons = []
  for row in raw_markup:
    raw_buttons = []
    for btn in row:
      text_ref = btn.text
      callback = btn.callback
      url = btn.url
      text = textify(text_ref, lang, use_b=True)
      check_callback_data(callback, label=f"Callback data for button '{text}' (Chat ID: {chat_id})")

      raw_buttons.append(InlineKeyboardButton(text = text, callback_data = callback, url = url))
    buttons.append(raw_buttons)
  return buttons


# --- For Main Screen messages ---

async def edit_message(session: Session, text: TextRef | list[TextRef], buttons: list[list[Button]] = None, parse_mode: str = None):
  user = await get_user_by_id(session.user_id)
  lang = user.lang
  text = textify(text, lang)

  raw_markup = buttons
  buttons = build_buttons(raw_markup, session.id, lang) if buttons else None

  if session.text == text and session.raw_markup == buttons:
    return False

  check_text_length(text, label=f"Message for Chat ID: {session.id}")

  markup = InlineKeyboardMarkup(buttons) if buttons else None

  out = await retry_async(
    lambda: session.bot.edit_message_text(
      chat_id = session.id, 
      message_id = session.message_id, 
      text = text, 
      reply_markup = markup, 
      parse_mode = parse_mode
      ), 
      f"Edit message (Chat ID: {session.id})"
    )
  
  if isinstance(out, Message):
    session.set_ui(text = text, raw_markup = raw_markup)

  return True


async def send_message(session: Session, text: TextRef | list[TextRef], buttons: list[list[Button]] = None, old_message: Message = None, delete_old_message: bool = False, parse_mode: str = None):
  if old_message and delete_old_message:
    await retry_async(lambda: old_message.delete(), f"Delete old message (Chat ID: {session.id})")

  user = await get_user_by_id(session.user_id)
  lang = user.lang
  text = textify(text, lang)

  raw_markup = buttons
  buttons = build_buttons(raw_markup, session.id, lang) if buttons else None
    
  check_text_length(text, label=f"Message for Chat ID: {session.id}")

  markup = InlineKeyboardMarkup(buttons) if buttons else None

  sent_msg = await retry_async(
    lambda: session.bot.send_message(
      chat_id = session.id,
      text = text,
      reply_markup = markup,
      parse_mode = parse_mode),
      f"Send message (Chat ID: {session.id})"
    )
  
  if isinstance(sent_msg, Message):
    session.message_id = sent_msg.message_id
    session.set_ui(text = text, raw_markup = raw_markup, parse_mode = parse_mode)
  
  return True


# TODO: Needs logging and handling edge cases. 
async def broadcast_message(game: Game, mode: str, text: TextRef | list[TextRef], buttons: list[list[Button]] = None, parse_mode: str = None, exclude_session_ids: list[int] = None, only_with_substate: AnySubstate = None):

  exclude_session_ids = exclude_session_ids or []

  if mode not in ["edit", "send"]:
    logger.warning(f"Invalid broadcasting mode: {mode}")
    return

  tasks = []
  sessions = get_all_sessions(game = game, excluded = exclude_session_ids)

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

async def send_popup_message(session: Session = None, text: TextRef | list[TextRef] = None, buttons: list[list[Button]] = None, target: Session | Game = None) -> Message:

  if not session: return
  chat_id = session.id
  bot = session.bot

  user = await get_user_by_id(session.user_id)
  lang = user.lang
  text = textify(text, lang)

  raw_markup = buttons
  buttons = build_buttons(raw_markup, session.id, lang) if buttons else None

  #Checking Limits
  check_text_length(text, label = f"Popup message (Chat ID: {chat_id})")

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
    chat_id = target.id
  else:  # Game
    owner_session = get_session_of_owner(game=target)
    if not owner_session: return
    bot = owner_session.bot
    chat_id = owner_session.id

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

async def send_info_message(bot: Bot, chat_id: int, text: TextRef | list[TextRef], buttons: list[list[Button]] = None, parse_mode: str = None, lang = "en") -> Message:
  """Sends a simple, non-tracked, non-interactive message with full checks."""
  # Not interactive most of the time ...

  if not lang:
    session = get_session_by_id(chat_id)
    if session:
      user = await get_user_by_id(session.user_id) 
      lang = user.lang

  text = textify(text, lang)
  buttons = build_buttons(buttons, chat_id, lang) if buttons else None

  check_text_length(text, label = f"Info message (Chat ID: {chat_id})")

  msg = await retry_async(
    lambda: bot.send_message(chat_id = chat_id, text = text, reply_markup = InlineKeyboardMarkup(buttons) if buttons else None, parse_mode = parse_mode),
    f"Send info message (Chat ID: {chat_id})"
  )
  return msg

# --- For Join Message ---

async def send_join_message(bot: Bot, chat_id: int, game_id: str, user: User):
  """Sends a join message with a button to join the game."""

  text = TextRef("invitation_message", {"user_username": user.username})
  text = textify(text, user.lang)
  
  reply_markup = [[Button(TextRef("join"), None, f"https://t.me/{BOT_USERNAME}?start={game_id}")]]
  buttons = build_buttons(reply_markup, chat_id, user.lang)

  check_text_length(text, label = f"Popup message (Chat ID: {chat_id})")

  markup = InlineKeyboardMarkup(buttons)
  msg = await retry_async(
    lambda: bot.send_message(
      chat_id = chat_id,
      text = text,
      reply_markup = markup
      ),
      f"Send message (Chat ID: {chat_id})"
    )

  return msg

