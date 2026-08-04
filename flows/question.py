from models.modes import GameMode
from flows.states import GameState
from flows.substates import QuestionSubstate
from telegram import Update
from flows.utils import *
from data.links import get_session_by_id, get_session_of_owner
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_end_questions_screen(session: Session, game: Game):
  if game.mode == GameMode.TEAMS:
    text = TextRef("ready_vote_teams")
  else:
    text = TextRef("ready_vote_outsider")

  buttons = [
    [Button(TextRef("start_voting"), "g:start_vote")],
    [Button(TextRef("extra_questions"), "g:extra_questions")],
  ]

  await edit_message(session, text, buttons)


async def render_ask_question_screen(asker_session: Session, game: Game):
  pair = game.pairs[game.turn_index]
  text = TextRef("ask_question", {"asker" : pair[0].name, "answerer" : pair[1].name})

  buttons = [
    [Button(TextRef("next"), "g:next")],
  ]

  if game.turn_index > 0:
    buttons.append([Button(TextRef("back"), "g:back")])

  await broadcast_message(game=game, mode="edit", text=text, exclude_session_ids=[asker_session.id])
  await edit_message(asker_session, text, buttons)


# --- dispatch ---

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
    await render_end_questions_screen(owner_session, game)
    return False

  # --- RENDER CURRENT STEP ---

  asker_session = get_session_by_id(game.pairs[game.turn_index][0].session_id)
  asker_session.waited = True
  await render_ask_question_screen(asker_session, game)
  return False