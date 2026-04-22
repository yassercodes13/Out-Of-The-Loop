from handlers.utils import *
from telegram import Update
from models.game import Game
from models.session import Session
from flows.states import GameState
from telegram.ext import ContextTypes
from flows.setup import handle_setup
from flows.vote import handle_voting
from flows.reveal import handle_reveal
from flows.results import handle_results
from flows.inform import handle_informing
from flows.question import handle_questioning
from flows.vote_words import handle_vote_words
from flows.guess_word import handle_guess_word
from data.runtime_manager import terminate_game
from flows.guess_teams import handle_guess_teams
from flows.guess_outsider import handle_guess_outsider

async def route_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game:Game = None, session:Session = None):
  state_changed = False
  query = update.callback_query

  # --- init game if not set ---
  if query and query.data == "s:setup_game":
    user, game = get_user_game(update) #Ensures user exists
    if game:
      terminate_game(game)

    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    game = create_game(user_id = user.id, username = user.username)
    session = set_session(chat_id = chat_id, message_id = message_id, game_id = game.id, user_id = user.id, bot = context.bot)
    game.state = GameState.SETUP

  # --- route to correct flow ---
  if game.state == GameState.SETUP:
    state_changed = await handle_setup(update, game, session)

  elif game.state == GameState.INFORM:
    state_changed = await handle_informing(update, game, session)

  elif game.state == GameState.QUESTION:
    state_changed = await handle_questioning(update, game, session)

  elif game.state == GameState.VOTE:
    state_changed = await handle_voting(update, game, session)

  elif game.state == GameState.REVEAL:
    state_changed = await handle_reveal(update, game, session)

  elif game.state == GameState.GUESS_WORD:
    state_changed = await handle_guess_word(update, game, session)

  elif game.state == GameState.GUESS_OUTSIDER:
    state_changed = await handle_guess_outsider(update, game, session)

  elif game.state == GameState.VOTE_WORDS:
    state_changed = await handle_vote_words(update, game, session)

  elif game.state == GameState.GUESS_TEAMS:
    state_changed = await handle_guess_teams(update, game, session)

  elif game.state == GameState.RESULTS:
    state_changed = await handle_results(update, game, session)

  # --- reroute on state change ---
  if state_changed:
    await route_game(update, context, game, session)