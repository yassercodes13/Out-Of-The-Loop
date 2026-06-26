from telegram import InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from flows.mode_settings import handle_mode_settings
from models.game import Game
from models.session import Session
from flows.states import GameState
from flows.substates import AnyCategorySettingsSubstate, ModeSettingsSubstate, LanguageSettingsSubstate
from flows.category_settings import handle_category_settings
from flows.language_settings import handle_language_settings
from flows.msg_utils import edit_message
from flows.setup import handle_setup
from flows.vote import handle_voting
from flows.reveal import handle_reveal
from flows.results import handle_results
from flows.inform import handle_informing
from flows.question import handle_questioning
from flows.vote_words import handle_vote_words
from flows.guess_word import handle_guess_word
from flows.guess_teams import handle_guess_teams
from flows.guess_outsider import handle_guess_outsider
from handlers.utils import get_user_game
from texts import set_lang, t, b
from data.runtime_manager import terminate_game, create_game, set_session, terminate_session

async def route_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game:Game = None, session:Session = None):
  state_changed = False
  query = update.callback_query
  data = query.data if query else None
  user = get_user_game(update)[0]
  set_lang(user.lang)

  # --- init game if not set ---
  if data == "s:setup_game":
    user, game = get_user_game(update) #Ensures user exists
    if game:
      terminate_game(game)

    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    game = create_game(user_id = user.id, username = user.username)
    session = set_session(chat_id = chat_id, message_id = message_id, game_id = game.id, user_id = user.id, bot = context.bot)
    game.state = GameState.SETUP
    
    state_changed = await handle_setup(update, game, session)

  # --- route to correct flow ---
  elif game:
    if game.state == GameState.SETUP:
      state_changed = await handle_setup(update, game, session)

    elif game.state == GameState.CATEGORY_SETTINGS:
      state_changed = await handle_category_settings(update, game, session)

    elif game.state == GameState.MODE_SETTINGS:
      state_changed = await handle_mode_settings(update, game, session)

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

  elif data and data.startswith("e:") or (session.game_substate in AnyCategorySettingsSubstate) or (session.game_substate == ModeSettingsSubstate.MAIN):
    
    if data == "e:done":
      buttons = [
        [InlineKeyboardButton(b("categories"), callback_data = "e:categories")],
        [InlineKeyboardButton(b("modes"), callback_data = "e:modes")],
        [InlineKeyboardButton(b("language"), callback_data = "e:language")],
        [InlineKeyboardButton(b("done"), callback_data = "e:done")],
      ]

      if session.game_substate is None:
        await edit_message(session, text = t("settings_saved"), buttons = buttons)
        terminate_session(session = session)
    
      else:
        await edit_message(session, text = t("choose_edit"), buttons = buttons)
        session.game_substate = None

    elif session.game_substate in AnyCategorySettingsSubstate or data == "e:categories":
      state_changed = await handle_category_settings(update, game, session)
  
    elif session.game_substate == ModeSettingsSubstate.MAIN or data == "e:modes":
      state_changed = await handle_mode_settings(update, game, session)
    
    elif session.game_substate == LanguageSettingsSubstate.MAIN or data == "e:language":
      state_changed = await handle_language_settings(update, session)

  # --- reroute on state change ---
  if state_changed:
    await route_game(update, context, game, session)