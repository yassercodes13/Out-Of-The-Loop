import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup,Message
from data.runtime_manager import *
from models.session import Session
from models.game import Game
from flows.substates import AnySubstate

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
  
  markup = InlineKeyboardMarkup(buttons) if buttons else None
  
  try:
    await session.bot.edit_message_text(chat_id = session.chat_id, message_id = session.message_id, text = text, reply_markup = markup, parse_mode = parse_mode)
    session.set_ui(text = text, raw_markup = raw_markup)
    return True
  except Exception as e:
    await asyncio.sleep(0.5)  # Wait a bit and try again
    await session.bot.edit_message_text(chat_id = session.chat_id, message_id = session.message_id, text = text, reply_markup = markup, parse_mode = parse_mode)
    session.set_ui(text = text, raw_markup = raw_markup)
    return True
  
      
async def send_message(session: Session, text: str, buttons: list[list[InlineKeyboardButton]] = None, old_message: Message = None, delete_old_message: bool = False, parse_mode: str = None):
  if old_message and delete_old_message:
    try:
      await old_message.delete()
    except Exception as e:
      await asyncio.sleep(0.5)
      await old_message.delete()
  
  markup = InlineKeyboardMarkup(buttons) if buttons else None
  
  try:
    sent_msg = await session.bot.send_message(chat_id = session.chat_id, text = text, reply_markup = markup, parse_mode = parse_mode)
    session.message_id = sent_msg.message_id
    session.set_ui(text = text, buttons = buttons)
    return True
  except Exception as e:
    await asyncio.sleep(0.5)
    sent_msg = await session.bot.send_message(chat_id = session.chat_id, text = text, reply_markup = markup, parse_mode = parse_mode)
    session.message_id = sent_msg.message_id
    session.set_ui(text = text, buttons = buttons)
    return True


async def broadcast_message(game: Game, mode: str, text: str, buttons: list[list[InlineKeyboardButton]] = None, parse_mode: str = None, exclude_chat_ids: list[int] = None, only_with_substate: AnySubstate = None):
  exclude_chat_ids = exclude_chat_ids or []
  
  if mode not in ["edit", "send"]:
    return
  
  tasks = []
  sessions = get_all_sessions(game = game, excluded = exclude_chat_ids)
  
  if only_with_substate:
    valid_sessions = []
    for session in sessions:
      if only_with_substate == session.game_substate:
        valid_sessions.append(session)
    sessions = valid_sessions
  
  for session in sessions:
    if mode == "edit":
      tasks.append(edit_message(session = session, text = text, buttons = buttons, parse_mode= parse_mode))
    elif mode == "send":
      tasks.append(send_message(session = session, text = text, buttons = buttons, parse_mode = parse_mode))

  if tasks:
    await asyncio.gather(*tasks, return_exceptions=True)


def set_all_substates(game: Game, substate, exclude_chat_ids: list[int] = None):
  exclude_chat_ids = exclude_chat_ids or []
  sessions: list[Session] = get_all_sessions(game = game, excluded = exclude_chat_ids) 
  
  for session in sessions:
    session.game_substate = substate


def reset_turn_indices(game, exclude_chat_ids: list[int] = None):
  exclude_chat_ids = exclude_chat_ids or []
  sessions = get_all_sessions(game = game, excluded = exclude_chat_ids)

  for session in sessions:
    session.turn_index = 0

def empty_slots(game: Game):
  sessions_with_no_players = 0
  for s in get_all_sessions(game = game):
    if len(s.players) == 0:
      sessions_with_no_players += 1
  empty_slots = game.initial_players_count - len(game.players) - sessions_with_no_players + 1  
  # the +1 because i will show that to an empty session always so the session may use the seat preserved to it
  return empty_slots