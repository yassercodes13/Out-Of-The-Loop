from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from data.users import get_user_by_id
from models.session import Session
from texts import t, b, set_lang, supported_langs
from flows.substates import LanguageSettingsSubstate
from flows.msg_utils import edit_message


async def handle_language_settings(update: Update, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = get_user_by_id(session.user_id)

  async def render_language_settings_screen():
    buttons = []
    for lang in supported_langs:
      mark = " ✅" if user.lang == lang else ""
      button = InlineKeyboardButton(text = b(f"language_{lang}") + mark, callback_data = f"e:language:{lang}")
      buttons.append([button])
    buttons.append([InlineKeyboardButton(b("done"), callback_data="e:done")])
    await edit_message(session = session, text = t("language_main") , buttons = buttons)

  if session.game_substate is None or data.startswith("e:language"):
    session.game_substate = LanguageSettingsSubstate.MAIN

  if session.game_substate == LanguageSettingsSubstate.MAIN:
    if data.startswith("e:language:"):
      lang = data.split(":")[-1]
      if lang in supported_langs:
        user.lang = lang
        set_lang(lang)

    elif data == "e:done":
      session.game_substate = None
      return True
    
    await render_language_settings_screen()

  return False