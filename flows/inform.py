from data.runtime_manager import get_session_of_owner
from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import InformSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *


async def handle_informing(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  
  # ---- STATE TRANSITIONS ----

  if data == "g:start_round" and session.game_substate is None: # Players start playing here
    game.sessions_ready = 0
    reset_turn_indices(game)
    text = game.start_round()
    buttons = [[InlineKeyboardButton("Got it!", callback_data="g:start_informing")]]

    set_all_substates(game, InformSubstate.ROUND_INFO)
    await broadcast_message(game = game, mode = "edit", text = text, buttons = buttons)
    return False

  elif data == "g:start_informing" and session.game_substate == InformSubstate.ROUND_INFO:
    session.game_substate = InformSubstate.HIDE

  elif data == "g:next" and session.game_substate in [InformSubstate.HIDE, InformSubstate.SHOW]:
    session.game_substate = InformSubstate.HIDE
    session.turn_index += 1

  elif data == "g:back" and session.game_substate == InformSubstate.HIDE and session.turn_index > 0:
    session.turn_index -= 1

  elif  data == "g:show" and session.game_substate == InformSubstate.HIDE:
    player = session.players[session.turn_index]
    player.saw_info += 1
    session.game_substate = InformSubstate.SHOW

    text = player.info()
    parse_mode = "HTML"
    buttons = [[InlineKeyboardButton("Got it!", callback_data="g:next")]]
    
    await edit_message(session, text, buttons, parse_mode)
    return False
  
  elif data == "g:start_question" and session.game_substate == InformSubstate.END:
    session.turn_index = 0
    game.state = GameState.QUESTION
    set_all_substates(game, None)
    return True

  # ---- END CONDITION ----
  if session.turn_index >= len(session.players) and session.game_substate != InformSubstate.END:
    session.game_substate = InformSubstate.END
    game.sessions_ready += 1
    
    extra_informs = "\n".join(
      f"{p.name} has seen their info {p.saw_info} times"
      for p in session.players if p.saw_info > 1
    )

    ready = False
    if game.sessions_ready >= len(game.chat_ids):
      ready = True

    waiting_text = ""
    if not ready:
      waiting_text = "Waiting for other players to finish..."
    
    text = ("All players informed!" + "\n\n" + extra_informs).strip()
    text += ("\n\n" + waiting_text)
    text.strip()


    if ready:
      text = "All players are ready!"
      buttons = [[InlineKeyboardButton("Start Questioning", callback_data="g:start_question")]]
      owner_session = get_session_of_owner(game=game)
      extra_informs = "\n".join(
        f"{p.name} has seen their info {p.saw_info} times"
        for p in owner_session.players if p.saw_info > 1
      )
      new_text = (extra_informs + "\n\n" + "All players ready").strip()
      await edit_message(owner_session, new_text, buttons)
      if session.user_id == owner_session.user_id:
        return False
    
    await edit_message(session, text)
    return False

  # ---- RENDER CURRENT STEP ----

  else:
    player = session.players[session.turn_index]
    session.game_substate = InformSubstate.HIDE
    
    buttons = [
      [InlineKeyboardButton("That's me!", callback_data = "g:show")]
    ]

    if session.turn_index > 0:
      buttons.append([InlineKeyboardButton("Back", callback_data = "g:back")])

    if player.saw_info > 0:
      buttons.append([InlineKeyboardButton("Skip", callback_data = "g:next")])

    text=f"Give phone to {player.name}"
    
    await edit_message(session, text, buttons)

    return False