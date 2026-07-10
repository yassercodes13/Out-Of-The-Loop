import logging

from telegram import InlineKeyboardButton
from config import TELEGRAM_MAX_TEXT_LENGTH, TELEGRAM_MAX_CALLBACK_DATA_BYTES, TELEGRAM_LENGTH_WARNING_THRESHOLD

logger = logging.getLogger(__name__)

def check_text_length(text: str, label: str = "message"):
  limit = TELEGRAM_MAX_TEXT_LENGTH
  length = len(text)
  if length > limit:
    logger.warning(f"{label} exceeds max length ({length}/{limit} chars) — Telegram will reject this")
  elif length > limit * TELEGRAM_LENGTH_WARNING_THRESHOLD:
    logger.warning(f"{label} is close to max length ({length}/{limit} chars)")


def check_callback_data(callback_data: str, label: str = "callback_data"):
  if callback_data is None:
    return
  
  size = len(callback_data.encode("utf-8"))
  limit = TELEGRAM_MAX_CALLBACK_DATA_BYTES
  if size > limit:
    logger.warning(f"{label} exceeds max callback_data size ({size}/{limit} bytes) — Telegram will reject this")
  elif size > limit * TELEGRAM_LENGTH_WARNING_THRESHOLD:
    logger.warning(f"{label} is close to max callback_data size ({size}/{limit} bytes)")

def check_buttons(buttons: list[list[InlineKeyboardButton]], chat_id: str = "buttons"):
  for row in buttons:
    for btn in row:
      check_callback_data(btn.callback_data, label=f"Callback data for button '{btn.text}' (Chat ID: {chat_id})")