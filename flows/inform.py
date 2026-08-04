from data.links import get_session_of_owner
from models.game import Game
from models.role import Role
from models.session import Session
from flows.states import GameState
from flows.substates import InformSubstate
from telegram import Update
from flows.utils import *
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_round_info_screen(game: Game):
  info = game.start_round(reset_mode = True)
  text = TextRef("round_info", {"round_number": info["round_number"], "category": info["category"], "mode": info["mode"]})

  buttons = [[Button(TextRef("got_it"), "g:start_informing")]]
  await broadcast_message(game = game, mode = "edit", text = text, buttons = buttons)

async def render_show_info_screen(session: Session):
  player = session.players[session.turn_index]
  
  if player.role == Role.DETECTIVE:
    text = TextRef("show_info_detective", 
      {
        "p_name": player.name,
        "p_role": TextRef(f"role_{player.role.value}"),
        "p_alpha_word": player.alpha_word,
        "p_beta_word": player.beta_word,
        "p_current_score": player.score
      }
    )
  
  else:
    text = TextRef("show_info_player",
      {
        "p_name" : player.name,
        "p_word" : player.word,
        "p_prefix" : TextRef("your_team") if player.role in [Role.ALPHA, Role.BETA] else TextRef("your_role"),
        "p_role" : TextRef(f"role_{player.role.value}"),
        "p_current_score" : player.score
      }
    )
  
  buttons = [[Button(TextRef("got_it"), "g:next")]]
  await edit_message(session, text, buttons)

async def render_end_inform_screen(session: Session, game: Game):
  ready = game.sessions_ready >= len(game.session_ids)
  extra_informs = [
    line
    for p in session.players
    if p.saw_info > 1
    for line in [
      TextRef("seen_info_times", {
        "p_name": p.name,
        "p_saw_info": p.saw_info
      }),
      TextRef("text", {"text": "\n"})
    ]
  ]

  if ready:
    owner_session = get_session_of_owner(game=game)
    extra_informs_owner = [
      line
      for p in owner_session.players
      if p.saw_info > 1
      for line in [
        TextRef("seen_info_times", {
          "p_name": p.name,
          "p_saw_info": p.saw_info
        }),
        TextRef("text", {"text": "\n"})
      ]
    ]
    new_text = extra_informs_owner + [TextRef("text", {"text" : "\n\n"}), TextRef("all_ready")]
    buttons = [[Button(TextRef("start_questioning"), "g:start_question")]]
    owner_session.waited = True
    await edit_message(owner_session, new_text, buttons)

    if session.user_id != owner_session.user_id:
      await edit_message(session, TextRef("all_ready"))
  else:
    waiting_text = TextRef("waiting_others_finish")
    text = [TextRef("all_informed"), TextRef("text", {"text":"\n\n"})] + extra_informs
    text += [TextRef("text", {"text":"\n\n"}), waiting_text]
    await edit_message(session, text)

async def render_hide_info_screen(session: Session):
  player = session.players[session.turn_index]
  buttons = [
    [Button(TextRef("thats_me"), "g:show")]
  ]

  if session.turn_index > 0:
    buttons.append([Button(TextRef("back"), "g:back")])

  if player.saw_info > 0:
    buttons.append([Button(TextRef("skip"), "g:next")])

  text = TextRef("give_phone_to", {"p_name" : player.name})
  await edit_message(session, text, buttons)

# --- dispatch ---

async def handle_informing(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  
  # ---- STATE TRANSITIONS ----

  if data == "g:start_round" and session.game_substate is None: 
    game.sessions_ready = 0
    reset_turn_indices(game)
    set_all_substates(game, InformSubstate.ROUND_INFO, set_waited = True)
    
    await render_round_info_screen(game)
    return False

  elif data == "g:start_informing" and session.game_substate == InformSubstate.ROUND_INFO:
    session.game_substate = InformSubstate.HIDE

  elif data == "g:next" and session.game_substate in [InformSubstate.HIDE, InformSubstate.SHOW]:
    session.game_substate = InformSubstate.HIDE
    session.turn_index += 1

  elif data == "g:back" and session.game_substate == InformSubstate.HIDE and session.turn_index > 0:
    session.turn_index -= 1

  elif data == "g:show" and session.game_substate == InformSubstate.HIDE:
    player = session.players[session.turn_index]
    player.saw_info += 1
    session.game_substate = InformSubstate.SHOW

    await render_show_info_screen(session)
    return False
  
  elif data == "g:start_question" and session.game_substate == InformSubstate.END:
    session.turn_index = 0
    game.state = GameState.QUESTION
    set_all_substates(game, None, set_waited = False)
    return True

  # ---- END CONDITION ----
  if session.turn_index >= len(session.players) and session.game_substate != InformSubstate.END:
    session.game_substate = InformSubstate.END
    game.sessions_ready += 1
    session.waited = False
    
    await render_end_inform_screen(session, game)
    return False

  # ---- RENDER CURRENT STEP ----

  else:
    session.game_substate = InformSubstate.HIDE
    await render_hide_info_screen(session)
    return False