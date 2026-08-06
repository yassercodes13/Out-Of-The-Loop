from telegram import Update
from data.users import get_user_by_id, update_user
from models.session import Session
from texts import supported_langs
from flows.substates import LanguageSettingsSubstate
from adapters.telegram.messaging import edit_message
from views.language_settings import render_language_settings_screen

async def handle_language_settings(update: Update, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = await get_user_by_id(session.user_id)

  if session.game_substate is None or data.startswith("e:language"):
    session.game_substate = LanguageSettingsSubstate.MAIN

  if session.game_substate == LanguageSettingsSubstate.MAIN:
    if data and data.startswith("e:language:"):
      lang = data.split(":")[-1]
      if lang in supported_langs:
        user.lang = lang

    elif data == "e:done":
      session.game_substate = None
      await update_user(user)
      return True

    screen = render_language_settings_screen(user.lang)
    await edit_message(session, screen.textref, screen.buttons)

  return False