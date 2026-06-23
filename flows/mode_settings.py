from telegram import InlineKeyboardButton, Update
from data.modes import GameMode
from flows.states import GameState
from flows.substates import ModeSettingsSubstate, SetupSubstate
from handlers.utils import get_user_game
from models.game import Game
from models.session import Session
from flows.msg_utils import *

async def handle_mode_settings(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = get_user_game(update)[0]

  if session.game_substate == None or data == "e:modes":
    session.game_substate = ModeSettingsSubstate.MAIN


  if session.game_substate == ModeSettingsSubstate.MAIN and (data == "e:modes" or data.startswith("e:toggle") or data.startswith("s:choose_mode") or data == "e:done"):
    user = get_user_by_id(update.effective_user.id)
    
    if data.startswith("e:toggle"):
      mode_txt = data.split(':')[2]
      mode = GameMode(mode_txt)

      if mode in user.random_modes:
        if len(user.random_modes) <= 2:
          await query.answer("You must have at least 2 modes selected for random mode.", show_alert=True)
          return False
        user.random_modes.remove(mode)
      else:
        user.random_modes.append(mode)
    
    elif data.startswith("s:choose_mode"):
      game.state = GameState.SETUP
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return True
    
    text = (
      "The modes you select here will be the only ones that show up when you choose random mode.\n"
      "You have to select at least 2 modes\n\n"
      f"To play with the current list of modes you must have at least {user.min_players_for_random} players."
    )
    buttons = [
      [InlineKeyboardButton(
        text = mode.label + (" ✔" if mode in user.random_modes else " ✘"),
        callback_data=f'e:toggle:{mode.value}'
      )] for mode in GameMode if mode != GameMode.RANDOM
    ]
    if game:
      buttons.append([InlineKeyboardButton(text = "Back to mode selection", callback_data=f's:choose_mode')])
    else:
      buttons.append([InlineKeyboardButton(text = "Back to Settings", callback_data=f'e:done')])

    await edit_message(session, text, buttons)


  return False