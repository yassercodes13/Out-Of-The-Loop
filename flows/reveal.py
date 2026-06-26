from models.game import Game
from models.session import Session
from data.modes import GameMode
from flows.states import GameState
from flows.substates import RevealSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *
from texts import t, b
from data.runtime_manager import get_session_of_owner, get_session_of_chat

# --- screen renderers ---

async def render_single_outsider_screen(game: Game):
  outsiders = game.outsiders
  text = t("single_outsider_reveal", name=outsiders[0].name)
  buttons = [
    [InlineKeyboardButton(b("guess_word"), callback_data ="g:guess_word:0")]
  ]
  outsider_session = get_session_of_chat(outsiders[0].session_id)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[outsider_session.chat_id])
  await edit_message(outsider_session, text, buttons)

async def render_double_outsider_screen(game: Game):
  outsiders = game.outsiders
  reveal_text = t("most_voted_outsider_reveal", name=outsiders[0].name)
  choices_text = reveal_text + t("double_outsider_choices", name=outsiders[0].name)

  buttons = [
    [InlineKeyboardButton(b("guess_word"), callback_data="g:guess_word:0")],
    [InlineKeyboardButton(b("guess_outsider"), callback_data="g:guess_outsider")]
  ]

  outsider_session = get_session_of_chat(outsiders[0].session_id)
  await broadcast_message(game=game, mode="edit", text=reveal_text, exclude_chat_ids=[outsider_session.chat_id])
  await edit_message(outsider_session, choices_text, buttons)

async def render_detective_reveal_screen(game: Game):
  text = t("detective_reveal", name=game.detective.name)
  buttons = [
    [InlineKeyboardButton(b("guess_team_members"), callback_data="g:guess_teams")]
  ]

  detective_session = get_session_of_chat(game.detective.session_id)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[detective_session.chat_id])
  await edit_message(detective_session, text, buttons)

async def render_teams_reveal_screen(game: Game):
  alphas_str = ', '.join([p.name for p in game.alphas])
  betas_str = ', '.join([p.name for p in game.betas])
  text = t("teams_reveal", alphas=alphas_str, betas=betas_str)
  buttons = [
    [InlineKeyboardButton(b("vote_words"), callback_data="g:vote_words")]
  ]

  owner_session = get_session_of_owner(game=game)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
  await edit_message(owner_session, text, buttons)


# --- dispatch ---

async def handle_reveal(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:reveal" and session.game_substate is None:
    game.sessions_ready = 0
    set_all_substates(game, RevealSubstate.SHOW_RESULT)
  
  if session.game_substate == RevealSubstate.CHOICE:      # Branching
    set_all_substates(game, None)
    if data == "g:guess_outsider":
      game.state = GameState.GUESS_OUTSIDER
      return True
    elif data and data.startswith("g:guess_word:"):
      game.state = GameState.GUESS_WORD
      return True
    elif data == "g:vote_words":
      game.state = GameState.VOTE_WORDS
      return True
    elif data == "g:guess_teams":
      game.state = GameState.GUESS_TEAMS
      return True

    return False

  if session.game_substate == RevealSubstate.SHOW_RESULT:

    outsiders = game.outsiders
    
    if len(outsiders) == 1:
      await render_single_outsider_screen(game)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False
    
    elif len(outsiders) == 2:
      await render_double_outsider_screen(game)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False

    elif game.mode == GameMode.TEAMS and game.detective:
      await render_detective_reveal_screen(game)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False
      
    elif game.mode == GameMode.TEAMS and not game.detective:
      await render_teams_reveal_screen(game)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False

    return False