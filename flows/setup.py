from flows.category_settings import make_category_buttons
from flows.utils import *
from flows.states import GameState
from flows.substates import SetupSubstate
from data.links import get_user_by_id, get_session_by_id, get_session_of_owner
from services.lifecycle_services import terminate_session
from handlers.utils import *
from data.default_categories import default_categories
from models.modes import GameMode
from config import MAX_ROUNDS, MIN_ROUNDS, PLAYER_COUNT_OPTIONS_PER_ROW, ROUND_ADJUST_STEPS, MAX_PLAYERS, MIN_PLAYERS
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button

# --- screen renderers ---

async def render_players_count_screen(session: Session):
  text = TextRef("choose_number_of_players")
  buttons = [
    [
      Button(TextRef("text", {"text": f"{i}"}), f"s:players:{i}"),
      Button(TextRef("text", {"text": f"{i+1}"}), f"s:players:{i+1}")
    ] for i in range(MIN_PLAYERS, MAX_PLAYERS, PLAYER_COUNT_OPTIONS_PER_ROW)
  ]
  await edit_message(session, text, buttons)


async def render_game_type_screen(session: Session):
  text = TextRef("choose_game_type")
  buttons = [
    [Button(TextRef("same_phone"), "s:game_type:single")],
    [Button(TextRef("multiple_phones"), "s:game_type:multiple")],
    [Button(TextRef("multiple_phones_help"), "s:game_type:help")]
  ]
  await edit_message(session, text, buttons)


async def render_game_type_help_screen(session: Session):
  text = TextRef("game_type_help")
  buttons = [[
    Button(TextRef("got_it"), "s:game_type:select")
  ]]
  await edit_message(session, text, buttons)


async def render_input_names_single_screen(session: Session, game: Game):
  text = TextRef("game_type_single", {"initial_players_count": game.initial_players_count})
  await edit_message(session, text)


async def render_input_names_multiple_screen(session: Session, game: Game):
  slots = empty_slots(game)
  text = TextRef("game_type_multiple", {"game_id": game.id, "slots": slots})
  await edit_message(session, text)

  user = await get_user_by_id(session.user_id)
  await send_join_message(
    bot = session.bot,
    chat_id = session.id,
    game_id = game.id,
    user = user
  )


async def render_adjust_rounds_screen(session: Session, game: Game, initial=False):
  text = TextRef("adjust_number_of_rounds" if initial else "current_number_of_rounds", {"num_rounds": game.num_rounds})

  buttons = []
  for step in ROUND_ADJUST_STEPS:
    row = []
    row.append(Button(TextRef("text", {"text": f"+{step}"}), f's:rounds:+{step}')) if game.num_rounds + step <= MAX_ROUNDS else None
    row.append(Button(TextRef("text", {"text": f"-{step}"}), f's:rounds:-{step}')) if game.num_rounds - step >= MIN_ROUNDS else None
    if row:
      buttons.append(row)

  buttons.append([Button(TextRef("perfect"), 's:rounds:done')])
  await edit_message(session, text, buttons)


async def render_choose_category_screen(session: Session, game: Game, user: User, start_idx = 0):
  text = TextRef("choose_category", {"num_rounds": game.num_rounds})
  buttons = make_category_buttons(start_idx, user, game.all_categories, callback_prefix="s:cat", show_random=True)
  buttons.append([Button(TextRef("random"), 's:cat:random')])
  buttons.append([Button(TextRef("category_settings"), 'e:categories')])
  await edit_message(session, text, buttons)


async def render_choose_mode_screen(session: Session, user: User, category_info = "", mode_change = False):
  if category_info != "":
    text = TextRef("choose_mode", {"category_info": category_info})

  elif mode_change:
    text = TextRef("mode_change_needed")

  buttons = [
    [Button(TextRef("text", {"text": mode.label + f" ({mode.min_players}{' R' if mode in user.random_modes else ''})"}),   f's:mode:{mode.name}')
    ] for mode in GameMode if mode != GameMode.RANDOM
  ]
  buttons.append([Button(TextRef("random_with_number", {"min_players_for_random": user.min_players_for_random}), f's:mode:{GameMode.RANDOM.name}')])
  buttons.append([Button(TextRef("edit_random"), f'e:modes')])
  await edit_message(session, text, buttons)


async def render_all_set_screen(session: Session, game: Game):
  text = TextRef("all_set", {"mode_label": game.mode.label})
  buttons = [[Button(TextRef("start_game"), 'g:start_round')]]
  await edit_message(session, text, buttons)


# --- dispatch ---

async def handle_setup(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if session.game_substate is None and query and data:
    session.game_substate = SetupSubstate.PLAYERS_COUNT
    session.waited = True
    await render_players_count_screen(session)
    return False

  if session.game_substate == SetupSubstate.PLAYERS_COUNT:
    if data.startswith("s:players:"):
      players_count = int(data.split(":")[2])
      game.initial_players_count = players_count

      session.game_substate = SetupSubstate.GAME_TYPE
      await render_game_type_screen(session)
      return False

  elif session.game_substate == SetupSubstate.GAME_TYPE:
    if data == "s:game_type:select":
      await render_game_type_screen(session)
      return False

    if data.startswith("s:game_type:"):
      game_type = data.split(":")[2]

      if game_type == "help":
        await render_game_type_help_screen(session)
        return False

      game.type = game_type
      session.game_substate = SetupSubstate.INPUT_NAMES

      if game.type == "single":
        await render_input_names_single_screen(session, game)
      elif game.type == "multiple":
        await render_input_names_multiple_screen(session, game)

      return False

  elif session.game_substate == SetupSubstate.INPUT_NAMES:
    if update.message and update.message.reply_to_message:
      player_names = update.message.text.split()
      slots = empty_slots(game)
      user = await get_user_by_id(session.user_id)

      if game.type == "single" and not (len(player_names) == game.initial_players_count):
        await send_popup_message(
          session = session,
          text = TextRef("min_players", {"initial_players_count": game.initial_players_count}),
          buttons = [[Button(TextRef("ok"), "i:ok")]],
          target = session
        )
        return False
      elif game.type == "multiple" and not (1 <= len(player_names) <= slots):
        await send_popup_message(
          session = session,
          text = TextRef("input_names_error", {"slots": slots}),
          buttons = [[Button(TextRef("ok"), "i:ok")]],
          target = session
        )
        return False

      session.prepare_players(player_names, game)
      session.game_substate = SetupSubstate.WAITING
      session.waited = False

      if game.type == "multiple":
        players_names = ', '.join([p.name for p in session.players])
        text = TextRef("names_confirmation_multiple", {"players_names": players_names, "game_id": game.id, "joined_players": len(game.players), "initial_players_count": game.initial_players_count})

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, None, old_message=old_message, delete_old_message=True)

        if len(game.players) == game.initial_players_count:
          buttons = [[Button(TextRef("continue"), 's:all_joined')]]
          owner_session = get_session_of_owner(game=game)
          owner_session.waited = True
          await edit_message(owner_session, TextRef("all_joined"), buttons)

          for sid in game.session_ids:
            session = get_session_by_id(sid)
            if session.game_substate == SetupSubstate.INPUT_NAMES:
              await terminate_session(session_id = sid)

        else:
          await broadcast_message(
            game=game, mode="edit",
            text=TextRef("waiting_for_players", {"game_id": game.id, "joined_players": len(game.players), "initial_players_count": game.initial_players_count}),
            exclude_session_ids=[session.id],
            only_with_substate=SetupSubstate.WAITING,
          )
          slots = empty_slots(game)
          await broadcast_message(
            game=game, mode="edit",
            text=TextRef("input_names", {"slots": slots}),
            exclude_session_ids=[session.id],
            only_with_substate=SetupSubstate.INPUT_NAMES,
          )

        return False

      elif game.type == "single":
        players_names = ', '.join([p.name for p in session.players])
        text = TextRef("names_confirmation_single", {"players_names": players_names})
        buttons = [[Button(TextRef("continue"), 's:all_joined')]]
        session.waited = True

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, buttons, old_message=old_message, delete_old_message=True)
        return False

  elif session.game_substate == SetupSubstate.WAITING:
    if query and data == "s:all_joined":
      await broadcast_message(game=game, mode="edit", text=TextRef("waiting_for_game_creator"), exclude_session_ids=[session.id])

      game.num_rounds = len(game.players)
      await render_adjust_rounds_screen(session, game, initial=True)

      session.game_substate = SetupSubstate.CHOOSE_ROUNDS
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_ROUNDS:
    if data.startswith("s:rounds:") and data != "s:rounds:done":
      rounds_count = game.num_rounds + int(data.split(':')[2])
      rounds_count = max(min(rounds_count, MAX_ROUNDS), MIN_ROUNDS)

      if game.num_rounds == rounds_count:
        return False

      game.num_rounds = rounds_count
      await render_adjust_rounds_screen(session, game)
      return False

    if data == "s:rounds:done":
      user = await get_user_by_id(update.effective_user.id)
      game.all_categories = user.generated_categories + default_categories
      await render_choose_category_screen(session, game, user)
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
        start_idx = max(0, min(start_idx, len(game.all_categories)-1))

      await render_choose_category_screen(session, game, user, start_idx)
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

      game.category = category
      title = "Random" if category is None else category.title
      category_info = TextRef("category_info", {"category_title":title})

      await render_choose_mode_screen(session, user, category_info)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_MODE:
    if data == "e:modes":
      game.state = GameState.MODE_SETTINGS
      session.game_substate = None
      return True

    if data == "s:choose_mode":
      user = await get_user_by_id(update.effective_user.id)
      category_info = TextRef("category_info", {"category_title": game.category.title if game.category else "Random"})
      await render_choose_mode_screen(session, user, category_info)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

    if data.startswith("s:mode:"):
      mode_name = data.split(':')[2]
      mode = GameMode[mode_name]

      if mode == GameMode.RANDOM:
        user = await get_user_by_id(update.effective_user.id)
        if user.min_players_for_random > len(game.players):
          await send_popup_message(
            session = session,
            text = TextRef("random_mode_min_players", {"min_players": user.min_players_for_random, "current_players": len(game.players)}),
            buttons = [[Button(TextRef("ok"), "i:ok")]],
            target = session
          )
          return False

      if mode.min_players > len(game.players):
        await send_popup_message(
          session = session,
          text = TextRef("mode_min_players", {"min_players": mode.min_players, "current_players": len(game.players)}),
          buttons = [[Button(TextRef("ok"), "i:ok")]],
          target = session
        )
        return False

      if mode == GameMode.RANDOM:
        user = await get_user_by_id(update.effective_user.id)
        game.random_mode_options = user.random_modes

      game.mode = mode
      await render_all_set_screen(session, game)
      session.game_substate = SetupSubstate.FINISHED
      return False

  elif session.game_substate == SetupSubstate.FINISHED:
    if data == "g:start_round":
      game.state = GameState.INFORM
      set_all_substates(game, None, set_waited = False)
      return True

  return False