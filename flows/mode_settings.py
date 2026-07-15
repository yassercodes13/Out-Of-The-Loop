from telegram import InlineKeyboardButton, Update
from data.modes import GameMode
from flows.states import GameState
from flows.substates import ModeSettingsSubstate, SetupSubstate
from models.game import Game
from models.session import Session
from flows.utils import *
from texts import t, b
from adapters.telegram.messaging import *

# --- screen renderers ---

async def render_mode_settings_screen(session: Session, game: Game, user):
  text = t("mode_settings_info", min_players = user.min_players_for_random)
  buttons = [
    [InlineKeyboardButton(
      text = mode.label + (" ✔" if mode in user.random_modes else " ✘"),
      callback_data=f'e:toggle:{mode.name}'
    )] for mode in GameMode if mode != GameMode.RANDOM
  ]
  if game:
    buttons.append([InlineKeyboardButton(b("back_to_mode_selection"), callback_data='s:choose_mode')])
  else:
    buttons.append([InlineKeyboardButton(b("back_to_settings"), callback_data='e:done')])

  await edit_message(session, text, buttons)


# --- dispatch ---

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
          await query.answer(t("min_two_modes"), show_alert=True)
          return False
        user.random_modes.remove(mode)
      else:
        user.random_modes.append(mode)

    elif data and data.startswith("s:choose_mode"):
      game.state = GameState.SETUP
      session.game_substate = SetupSubstate.CHOOSE_MODE
      await update_user(user)
      return True

    await render_mode_settings_screen(session, game, user)

  return False