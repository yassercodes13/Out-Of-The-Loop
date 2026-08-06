import logging
from telegram import Update
from telegram.ext import ContextTypes
from data.games import get_game_by_id
from models import Game, Session, User
from data.links import get_game_of_user
from data.users import get_user_by_id, update_user
from views.common import render_not_active_screen
from views.settings import render_settings_menu_screen, render_settings_saved_screen
from adapters.telegram.messaging import delete_popup, edit_message, send_info_message
from services.lifecycle_services import create_game, remove_players, set_session, terminate_session
from flows.states import GameState
from flows.setup import handle_setup
from flows.vote import handle_voting
from flows.reveal import handle_reveal
from flows.paused import handle_paused
from flows.results import handle_results
from flows.inform import handle_informing
from flows.question import handle_questioning
from flows.guess_word import handle_guess_word
from flows.vote_words import handle_vote_words
from flows.guess_teams import handle_guess_teams
from flows.mode_settings import handle_mode_settings
from flows.choose_player import handle_choose_player
from flows.guess_outsider import handle_guess_outsider
from flows.category_settings import handle_category_settings
from flows.language_settings import handle_language_settings
from flows.substates import AnyCategorySettingsSubstate, InterruptSubstate, ModeSettingsSubstate, LanguageSettingsSubstate

logger = logging.getLogger(__name__)


async def route_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: Game = None, session: Session = None, user: User = None):
  state_changed = False
  query = update.callback_query
  data = query.data if query else None
  if user is None:
    user = await get_user_by_id(update.effective_user.id)
    if user is None:
      return
  if game is None:
    game = await get_game_of_user(user.id)

  logger.info(f"User {user.id} | game: {game.id if game else None} | state: {game.state if game else None} | data: {data}")

  popups = []
  if game and game.popup_message_id: popups.append(game.popup_message_id)
  if session and session.popup_message_id: popups.append(session.popup_message_id)
  
  # --- interruptions ---
  if session and session.interrupt_substate == InterruptSubstate.REMOVE_PLAYER:
    if query.message.message_id not in popups:
      screen = render_not_active_screen()
      await send_info_message(
        bot = context.bot,
        chat_id = update.effective_chat.id,
        text = screen.textref,
        lang = user.lang
      )
      return
    state_changed = await handle_choose_player(update, game, session)

  elif session and session.interrupt_substate is None and data and data.startswith("i:"):
    if query.message.message_id not in popups:
      screen = render_not_active_screen()
      await send_info_message(
        bot = context.bot,
        chat_id = update.effective_chat.id,
        text = screen.textref,
        lang = user.lang
      )
      return

    if session and data == "i:session_alive":
      await delete_popup(session)
    if game and data == "i:game_running":
      await delete_popup(game)
    if session and data == "i:ok":
      await delete_popup(session)
  
  # --- init a game ---
  elif data == "s:setup_game":
    if user.game_id and session:
      old_game = get_game_by_id(user.game_id)
      if old_game:
        await remove_players(game = old_game, player_ids = [p.id for p in session.players])

    chat_id    = update.effective_chat.id
    message_id = update.effective_message.message_id

    session    = await set_session(id = chat_id, message_id = message_id, user_id = user.id, bot = context.bot, job_queue = context.job_queue)
    game       = await create_game(owner = user, owner_session = session, )
    session.waited = True
    game.set_reminder(context)

    game.state = GameState.SETUP
    logger.info(f"Game {game.id} created by user {user.id}")

    state_changed = await handle_setup(update, game, session)

  # --- route to correct flow within a game ---
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

    elif game.state == GameState.PAUSED:
      state_changed = await handle_paused(update, game, session)

  # --- Edits/Settings --- 

  elif data and data.startswith("e:") or (session.game_substate in AnyCategorySettingsSubstate) or (session.game_substate == ModeSettingsSubstate.MAIN):

    if data == "e:done":
      if session.game_substate is None:
        # Standalone settings session
        screen = render_settings_saved_screen()
        await edit_message(session, screen.textref, screen.buttons)
        await terminate_session(session_id=session.id)
      else:
        # Coming back from sub-settings (categories/modes/language) inside a game
        await update_user(user)
        screen = render_settings_menu_screen()
        await edit_message(session, screen.textref, screen.buttons)
        session.game_substate = None

    elif session.game_substate in AnyCategorySettingsSubstate or data == "e:categories":
      state_changed = await handle_category_settings(update, game, session)

    elif session.game_substate == ModeSettingsSubstate.MAIN or data == "e:modes":
      state_changed = await handle_mode_settings(update, game, session)

    elif session.game_substate == LanguageSettingsSubstate.MAIN or data == "e:language":
      state_changed = await handle_language_settings(update, session)

  # --- reroute on state change ---
  if state_changed:
    if game:
      logger.info(f"Game {game.id} state changed to {game.state}")
    await route_game(update, context, game, session, user)