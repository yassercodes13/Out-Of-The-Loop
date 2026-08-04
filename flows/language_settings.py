from telegram import Update
from data.users import get_user_by_id, update_user
from models.session import Session
from texts import supported_langs
from flows.substates import LanguageSettingsSubstate
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button


async def handle_language_settings(update: Update, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = await get_user_by_id(session.user_id)

  async def render_language_settings_screen():
    buttons = []
    for lang in supported_langs:
      chosen = "_chosen" if user.lang == lang else ""
      button = Button(TextRef(f"language_{lang}{chosen}"), f"e:language:{lang}")
      buttons.append([button])
    buttons.append([Button(TextRef("done"), "e:done")])
    await edit_message(session = session, text = TextRef("language_main"), buttons = buttons)

  if session.game_substate is None or data.startswith("e:language"):
    session.game_substate = LanguageSettingsSubstate.MAIN

  if session.game_substate == LanguageSettingsSubstate.MAIN:
    if data.startswith("e:language:"):
      lang = data.split(":")[-1]
      if lang in supported_langs:
        user.lang = lang

    elif data == "e:done":
      session.game_substate = None
      await update_user(user)
      return True
    
    await render_language_settings_screen()

  return False