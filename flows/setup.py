from flows.states import GameState
from flows.substates import SetupSubstate
from flows.utils import empty_slots, set_all_substates
from data.links import get_user_by_id, get_session_by_id, get_session_of_owner
from services.lifecycle_services import terminate_session
from telegram import Update
from models import Game, Session
from data.default_categories import default_categories
from models.modes import GameMode
from adapters.telegram.messaging import edit_message, send_message, send_join_message, send_popup_message, broadcast_message
from views import setup as setup_view
from config import MAX_ROUNDS, MIN_ROUNDS

async def handle_setup(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if session.game_substate is None and query and data:
    session.game_substate = SetupSubstate.PLAYERS_COUNT
    session.waited = True
    screen = setup_view.render_players_count_screen()
    await edit_message(session, screen.textref, screen.buttons)
    return False

  if session.game_substate == SetupSubstate.PLAYERS_COUNT:
    if data.startswith("s:players:"):
      players_count = int(data.split(":")[2])
      game.initial_players_count = players_count

      session.game_substate = SetupSubstate.GAME_TYPE
      screen = setup_view.render_game_type_screen()
      await edit_message(session, screen.textref, screen.buttons)
      return False

  elif session.game_substate == SetupSubstate.GAME_TYPE:
    if data == "s:game_type:select":
      screen = setup_view.render_game_type_screen()
      await edit_message(session, screen.textref, screen.buttons)
      return False

    if data.startswith("s:game_type:"):
      game_type = data.split(":")[2]

      if game_type == "help":
        screen = setup_view.render_game_type_help_screen()
        await edit_message(session, screen.textref, screen.buttons)
        return False

      game.type = game_type
      session.game_substate = SetupSubstate.INPUT_NAMES

      if game.type == "single":
        screen = setup_view.render_input_names_single_screen(game.initial_players_count)
        await edit_message(session, screen.textref, screen.buttons)

      elif game.type == "multiple":
        slots = empty_slots(game)
        screen = setup_view.render_input_names_multiple_screen(game.id, slots)
        await edit_message(session, screen.textref, screen.buttons)

        user = await get_user_by_id(session.user_id)
        await send_join_message(bot=session.bot, chat_id=session.id, game_id=game.id, user=user)

      return False

  elif session.game_substate == SetupSubstate.INPUT_NAMES:
    if update.message and update.message.reply_to_message:
      player_names = update.message.text.split()
      slots = empty_slots(game)

      if game.type == "single" and not (len(player_names) == game.initial_players_count):
        screen = setup_view.render_min_players_popup(game.initial_players_count)
        await send_popup_message(session=session, text=screen.textref, buttons=screen.buttons, target=session)
        return False
      elif game.type == "multiple" and not (1 <= len(player_names) <= slots):
        screen = setup_view.render_input_names_error_popup(slots)
        await send_popup_message(session=session, text=screen.textref, buttons=screen.buttons, target=session)
        return False

      session.prepare_players(player_names, game)
      session.game_substate = SetupSubstate.WAITING
      session.waited = False

      if game.type == "multiple":
        players_names = ', '.join([p.name for p in session.players])
        screen = setup_view.render_names_confirmation_multiple_screen(
          players_names, game.id, len(game.players), game.initial_players_count
        )
        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, screen.textref, screen.buttons, old_message=old_message, delete_old_message=True)

        if len(game.players) == game.initial_players_count:
          screen = setup_view.render_all_joined_screen()
          owner_session = get_session_of_owner(game=game)
          owner_session.waited = True
          await edit_message(owner_session, screen.textref, screen.buttons)

          for sid in game.session_ids:
            member_session = get_session_by_id(sid)
            if member_session.game_substate == SetupSubstate.INPUT_NAMES:
              await terminate_session(session_id=sid)

        else:
          screen = setup_view.render_waiting_for_players_screen(game.id, len(game.players), game.initial_players_count)
          await broadcast_message(
            game=game, mode="edit",
            text=screen.textref, buttons=screen.buttons,
            exclude_session_ids=[session.id],
            only_with_substate=SetupSubstate.WAITING,
          )

          slots = empty_slots(game)
          screen = setup_view.render_input_names_broadcast_screen(slots)
          await broadcast_message(
            game=game, mode="edit",
            text=screen.textref, buttons=screen.buttons,
            exclude_session_ids=[session.id],
            only_with_substate=SetupSubstate.INPUT_NAMES,
          )

        return False

      elif game.type == "single":
        players_names = ', '.join([p.name for p in session.players])
        screen = setup_view.render_names_confirmation_single_screen(players_names)
        session.waited = True

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, screen.textref, screen.buttons, old_message=old_message, delete_old_message=True)
        return False

  elif session.game_substate == SetupSubstate.WAITING:
    if query and data == "s:all_joined":
      screen = setup_view.render_waiting_for_game_creator_screen()
      await broadcast_message(game=game, mode="edit", text=screen.textref, buttons=screen.buttons, exclude_session_ids=[session.id])

      game.num_rounds = len(game.players)
      screen = setup_view.render_adjust_rounds_screen(game.num_rounds, initial=True)
      await edit_message(session, screen.textref, screen.buttons)

      session.game_substate = SetupSubstate.CHOOSE_ROUNDS
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_ROUNDS:
    if data.startswith("s:rounds:") and data != "s:rounds:done":
      rounds_count = game.num_rounds + int(data.split(':')[2])
      rounds_count = max(min(rounds_count, MAX_ROUNDS), MIN_ROUNDS)

      if game.num_rounds == rounds_count:
        return False

      game.num_rounds = rounds_count
      screen = setup_view.render_adjust_rounds_screen(game.num_rounds)
      await edit_message(session, screen.textref, screen.buttons)
      return False

    if data == "s:rounds:done":
      user = await get_user_by_id(update.effective_user.id)
      game.all_categories = user.generated_categories + default_categories
      screen = setup_view.render_choose_category_screen(game, user)
      await edit_message(session, screen.textref, screen.buttons)
      session.game_substate = SetupSubstate.CHOOSE_CATEGORY
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_CATEGORY:
    if data == "e:categories":
      game.state = GameState.CATEGORY_SETTINGS
      session.game_substate = None
      return True

    if data == "s:choose_category" or data.startswith("s:next_cats:"):
      user = await get_user_by_id(update.effective_user.id)
      game.all_categories = user.generated_categories + default_categories

      start_idx = 0
      if data.startswith("s:next_cats:"):
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(game.all_categories) - 1))

      screen = setup_view.render_choose_category_screen(game, user, start_idx)
      await edit_message(session, screen.textref, screen.buttons)
      session.game_substate = SetupSubstate.CHOOSE_CATEGORY
      return False

    if data.startswith("s:cat:"):
      user = await get_user_by_id(update.effective_user.id)

      category_idx = data.split(':')[2]
      if category_idx != "random":
        category = game.all_categories[int(category_idx)]
      else:
        game.random_category_options = user.random_categories
        category = None

      category_info = "Random" if game.category is None else category.title

      screen = setup_view.render_choose_mode_screen(user, category_info)
      await edit_message(session, screen.textref, screen.buttons)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_MODE:
    if data == "e:modes":
      game.state = GameState.MODE_SETTINGS
      session.game_substate = None
      return True

    if data == "s:choose_mode":
      user = await get_user_by_id(update.effective_user.id)
      category_info = game.category.title if game.category else "Random"
      screen = setup_view.render_choose_mode_screen(user, category_info)
      await edit_message(session, screen.textref, screen.buttons)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

    if data.startswith("s:mode:"):
      mode_name = data.split(':')[2]
      mode = GameMode[mode_name]

      if mode == GameMode.RANDOM:
        user = await get_user_by_id(update.effective_user.id)
        if user.min_players_for_random > len(game.players):
          screen = setup_view.render_random_mode_min_players_popup(user.min_players_for_random, len(game.players))
          await send_popup_message(session=session, text=screen.textref, buttons=screen.buttons, target=session)
          return False

      if mode.min_players > len(game.players):
        screen = setup_view.render_mode_min_players_popup(mode.min_players, len(game.players))
        await send_popup_message(session=session, text=screen.textref, buttons=screen.buttons, target=session)
        return False

      if mode == GameMode.RANDOM:
        game.random_mode_options = user.random_modes

      game.mode = mode
      screen = setup_view.render_all_set_screen(game.mode.label)
      await edit_message(session, screen.textref, screen.buttons)
      session.game_substate = SetupSubstate.FINISHED
      return False

  elif session.game_substate == SetupSubstate.FINISHED:
    if data == "g:start_round":
      game.state = GameState.INFORM
      set_all_substates(game, None, set_waited=False)
      return True

  return False