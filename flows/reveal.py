from models.game import Game
from models.session import Session
from models.modes import GameMode
from flows.states import GameState
from flows.substates import RevealSubstate
from telegram import Update
from flows.utils import *
from data.links import get_session_of_owner, get_session_by_id
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_single_outsider_screen(game: Game):
  outsiders = game.outsiders
  text = TextRef("single_outsider_reveal", {"name" : outsiders[0].name})
  buttons = [
    [Button(TextRef("guess_word"), "g:guess_word:0")]
  ]
  outsider_session = get_session_by_id(outsiders[0].session_id)
  outsider_session.waited = True

  await broadcast_message(game=game, mode="edit", text=text, exclude_session_ids=[outsider_session.id])
  await edit_message(outsider_session, text, buttons)

async def render_double_outsider_screen(game: Game):
  outsiders = game.outsiders
  reveal_text = [
    TextRef("most_voted_outsider_reveal", {"name":outsiders[0].name})
  ]

  choices_text = reveal_text + [TextRef("double_outsider_choices", {"name":outsiders[0].name})]

  buttons = [
    [Button(TextRef("guess_word"), "g:guess_word:0")],
    [Button(TextRef("guess_outsider"), "g:guess_outsider")]
  ]

  outsider_session = get_session_by_id(outsiders[0].session_id)
  outsider_session.waited = True
  await broadcast_message(game=game, mode="edit", text=reveal_text, exclude_session_ids=[outsider_session.id])
  await edit_message(outsider_session, choices_text, buttons)

async def render_detective_reveal_screen(game: Game):
  text = TextRef("detective_reveal", {"name" : game.detective.name})
  buttons = [
    [Button(TextRef("guess_team_members"), "g:guess_teams")]
  ]

  detective_session = get_session_by_id(game.detective.session_id)
  detective_session.waited = True
  await broadcast_message(game=game, mode="edit", text=text, exclude_session_ids=[detective_session.id])
  await edit_message(detective_session, text, buttons)

async def render_teams_reveal_screen(game: Game):
  alphas_str = ', '.join([p.name for p in game.alphas])
  betas_str = ', '.join([p.name for p in game.betas])
  text = TextRef("teams_reveal", {"alphas" : alphas_str, "betas" : betas_str})
  buttons = [
    [Button(TextRef("vote_words"), "g:vote_words")]
  ]

  owner_session = get_session_of_owner(game = game)
  owner_session.waited = True
  await broadcast_message(game=game, mode="edit", text=text, exclude_session_ids=[owner_session.id])
  await edit_message(owner_session, text, buttons)


# --- dispatch ---

async def handle_reveal(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:reveal" and session.game_substate is None:
    game.sessions_ready = 0
    outsiders = game.outsiders
    set_all_substates(game, RevealSubstate.CHOICE, set_waited = False)

    if len(outsiders) == 1:
      await render_single_outsider_screen(game)
    
    elif len(outsiders) == 2:
      await render_double_outsider_screen(game)

    elif game.mode == GameMode.TEAMS and game.detective:
      await render_detective_reveal_screen(game)
      
    elif game.mode == GameMode.TEAMS and not game.detective:
      await render_teams_reveal_screen(game)

    return False
  
  elif session.game_substate == RevealSubstate.CHOICE:      # Branching
    set_all_substates(game, None, set_waited = False)
    if data and data.startswith("g:guess_word:"):
      game.state = GameState.GUESS_WORD
    elif data == "g:guess_outsider":
      game.state = GameState.GUESS_OUTSIDER
    elif data == "g:vote_words":
      game.state = GameState.VOTE_WORDS
    elif data == "g:guess_teams":
      game.state = GameState.GUESS_TEAMS

    return True