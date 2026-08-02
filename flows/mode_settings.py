from telegram import Update
from data.modes import GameMode
from flows.states import GameState
from flows.substates import ModeSettingsSubstate, SetupSubstate
from models.game import Game
from models.session import Session
from flows.utils import *
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_mode_settings_screen(session: Session, game: Game, user: User):
  text = TextRef("mode_settings_info", {"min_players": user.min_players_for_random})
  buttons = [
    [(
      Button(TextRef("text", {"text" : mode.label + (" ✔" if mode in user.random_modes else " ✘")}),
      f'e:toggle:{mode.name}')
    )] for mode in GameMode if mode != GameMode.RANDOM
  ]
  if game:
    buttons.append([Button(TextRef("back_to_mode_selection"), 's:choose_mode')])
  else:
    buttons.append([Button(TextRef("back_to_settings"), 'e:done')])

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
          await query.answer()
          await send_popup_message(session, TextRef("min_two_modes"), [[Button(TextRef("ok"), "e:done")]], target = session)
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