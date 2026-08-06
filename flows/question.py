from models import Game, Session
from flows.states import GameState
from flows.substates import QuestionSubstate
from telegram import Update
from flows.utils import set_all_substates
from data.links import get_session_by_id, get_session_of_owner
from adapters.telegram.messaging import edit_message, broadcast_message
from views.question import render_end_questions_screen, render_ask_question_screen, render_waiting_for_owner_screen

async def handle_questioning(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data

  # --- STATE TRANSITIONS ---

  if data == 'g:start_question':
    game.turn_index = 0
    set_all_substates(game, QuestionSubstate.ASK)

  elif data == 'g:next':
    session.waited = False
    game.turn_index += 1

  elif data == 'g:back':
    session.waited = False
    game.turn_index -= 1
    game.turn_index = max(0, game.turn_index)

  elif data == "g:start_vote":
    session.waited = False
    game.state = GameState.VOTE
    set_all_substates(game, None, set_waited=False)
    return True

  elif data == "g:extra_questions":
    session.waited = False
    game.pair_players()
    game.turn_index = 0

  # --- END CONDITION ---

  if game.turn_index >= len(game.pairs):
    owner_session = get_session_of_owner(game=game)
    set_all_substates(game, QuestionSubstate.END)
    owner_session.waited = True

    # Owner gets the end screen with voting options
    screen_owner = render_end_questions_screen(game.mode)
    await edit_message(owner_session, screen_owner.textref, screen_owner.buttons)

    # Others get a waiting screen (no buttons)
    screen_others = render_waiting_for_owner_screen()
    await broadcast_message(
      game=game,
      mode="edit",
      text=screen_others.textref,
      exclude_session_ids=[owner_session.id]
    )
    return False

  # --- RENDER CURRENT STEP (if not end) ---

  pair = game.pairs[game.turn_index]
  asker_session = get_session_by_id(pair[0].session_id)
  asker_session.waited = True

  show_back = (game.turn_index > 0)
  screen = render_ask_question_screen(pair[0].name, pair[1].name, show_back)

  # Broadcast to others (text only, no buttons)
  await broadcast_message(
    game=game,
    mode="edit",
    text=screen.textref,
    exclude_session_ids=[asker_session.id]
  )

  # Edit the asker with full screen (text + buttons)
  await edit_message(asker_session, screen.textref, screen.buttons)

  return False