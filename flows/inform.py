from data.links import get_session_of_owner
from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import InformSubstate
from telegram import Update
from flows.utils import reset_turn_indices, set_all_substates
from adapters.telegram.messaging import broadcast_message, edit_message
from texts.refs import BroadcastScreens, TextRef
from views.inform import (
  render_round_info_screen,
  render_show_info_screen,
  render_hide_info_screen,
  render_end_inform_screen,
)


async def handle_informing(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  # ---- STATE TRANSITIONS ----

  if data == "g:start_round" and session.game_substate is None:
    game.sessions_ready = 0
    reset_turn_indices(game)
    set_all_substates(game, InformSubstate.ROUND_INFO, set_waited=True)

    # Render round info and broadcast to all
    info = game.start_round(reset_mode=True)
    screen = render_round_info_screen(info["round_number"], info["category"], info["mode"])
    await broadcast_message(game=game, mode="edit", text=screen.textref, buttons=screen.buttons)
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

    screen = render_show_info_screen(player)
    await edit_message(session, screen.textref, screen.buttons)
    return False

  elif data == "g:start_question" and session.game_substate == InformSubstate.END:
    session.turn_index = 0
    game.state = GameState.QUESTION
    set_all_substates(game, None, set_waited=False)
    return True

  # ---- END CONDITION ----
  if session.turn_index >= len(session.players) and session.game_substate != InformSubstate.END:
    session.game_substate = InformSubstate.END
    game.sessions_ready += 1
    session.waited = False

    # Prepare extra informs (players who saw info more than once)
    extra_informs = [
      line
      for p in session.players
      if p.saw_info > 1
      for line in [
        TextRef("seen_info_times", {"p_name": p.name, "p_saw_info": p.saw_info}),
        TextRef("text", {"text": "\n"})
      ]
    ]

    all_ready = (game.sessions_ready >= len(game.session_ids))

    result = render_end_inform_screen(all_ready, extra_informs)

    if isinstance(result, BroadcastScreens):
      # Owner gets special screen with button; others get text only
      owner_session = get_session_of_owner(game=game)
      owner_session.waited = True
      await edit_message(owner_session, result.special.textref, result.special.buttons)
      # Broadcast to others
      await broadcast_message(
        game=game,
        mode="edit",
        text=result.others.textref,
        exclude_session_ids=[owner_session.id]
      )
    else:
      # Not all ready: everyone sees the same waiting screen
      await edit_message(session, result.textref, result.buttons)

    return False

  # ---- RENDER CURRENT STEP (HIDE) ----
  else:
    session.game_substate = InformSubstate.HIDE
    player = session.players[session.turn_index]
    has_seen = (player.saw_info > 0)
    screen = render_hide_info_screen(
      player,
      session.turn_index,
      has_seen
    )
    await edit_message(session, screen.textref, screen.buttons)
    return False