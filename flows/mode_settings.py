from telegram import Update
from models.modes import GameMode
from flows.states import GameState
from flows.substates import ModeSettingsSubstate, SetupSubstate
from models.game import Game
from models.session import Session
from data.users import get_user_by_id, update_user
from adapters.telegram.messaging import edit_message, send_popup_message
from views.mode_settings import render_mode_settings_screen, render_min_two_modes_popup


async def handle_mode_settings(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if session.game_substate is None or data == "e:modes":
    session.game_substate = ModeSettingsSubstate.MAIN

  if session.game_substate == ModeSettingsSubstate.MAIN:
    user = await get_user_by_id(update.effective_user.id)

    if data and data.startswith("e:toggle"):
      mode_name = data.split(':')[2]
      mode = GameMode[mode_name]

      if mode in user.random_modes:
        if len(user.random_modes) <= 2:
          await query.answer()
          screen = render_min_two_modes_popup()
          await send_popup_message(session, screen.textref, screen.buttons, target=session)
          return False
        user.random_modes.remove(mode)
      else:
        user.random_modes.append(mode)

    elif data and data.startswith("s:choose_mode"):
      game.state = GameState.SETUP
      session.game_substate = SetupSubstate.CHOOSE_MODE
      await update_user(user)
      return True

    # Render screen
    show_back_to_game = (game is not None)
    screen = render_mode_settings_screen(user, show_back_to_game)
    await edit_message(session, screen.textref, screen.buttons)

  return False