from flows.category_settings import make_category_buttons
from flows.utils import *
from flows.states import GameState
from flows.substates import SetupSubstate
from telegram import InlineKeyboardButton
from data.runtime_manager import *
from handlers.utils import *
from data.default_categories import default_categories
from data.modes import GameMode
from config import BOT_USERNAME, MAX_ROUNDS, MIN_ROUNDS, PLAYER_COUNT_OPTIONS_PER_ROW, ROUND_ADJUST_STEPS, MAX_PLAYERS, MIN_PLAYERS
from texts import t, b
from adapters.telegram.messaging import *



# --- screen renderers ---

async def render_players_count_screen(session: Session):
  text = t("choose_number_of_players")
  buttons = [
    [
      InlineKeyboardButton(text=f"{i}", callback_data=f"s:players:{i}"),
      InlineKeyboardButton(text=f"{i+1}", callback_data=f"s:players:{i+1}")
    ] for i in range(MIN_PLAYERS, MAX_PLAYERS, PLAYER_COUNT_OPTIONS_PER_ROW)
  ]
  await edit_message(session, text, buttons)


async def render_game_type_screen(session: Session):
  text = t("choose_game_type")
  buttons = [
    [InlineKeyboardButton(text = b("same_phone"), callback_data = "s:game_type:single")],
    [InlineKeyboardButton(text = b("multiple_phones"), callback_data = "s:game_type:multiple")],
    [InlineKeyboardButton(text = b("multiple_phones_help"), callback_data="s:game_type:help")]
  ]
  await edit_message(session, text, buttons)


async def render_game_type_help_screen(session: Session):
  text = t("game_type_help")
  buttons = [[InlineKeyboardButton(text=b("got_it"), callback_data="s:game_type:select")]]
  await edit_message(session, text, buttons)


async def render_input_names_single_screen(session: Session, game: Game):
  text = t("game_type_single", initial_players_count=game.initial_players_count)
  await edit_message(session, text)


async def render_input_names_multiple_screen(session: Session, game: Game):
  slots = empty_slots(game)
  text = t("game_type_multiple", game_id=game.id, slots=slots)
  await edit_message(session, text)

  user = get_user_by_id(session.user_id)
  await session.bot.send_message(
    chat_id=session.chat_id,
    text=t("invitation_message", user_username=user.username),
    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(b("join"), url=f"https://t.me/{BOT_USERNAME}?start={game.id}")]])
  )


async def render_adjust_rounds_screen(session: Session, game: Game, initial=False):
  text = t("adjust_number_of_rounds" if initial else "current_number_of_rounds", num_rounds=game.num_rounds)

  buttons = []
  for step in ROUND_ADJUST_STEPS:
    buttons.append([
      InlineKeyboardButton(f"+{step}", callback_data = f's:rounds:+{step}'),
      InlineKeyboardButton(f"-{step}", callback_data = f's:rounds:-{step}'),
    ])

  filtered = []
  for row in buttons:
    new_row = []
    for btn in row:
      if "+" in btn.text and game.num_rounds == MAX_ROUNDS:
        continue
      if "-" in btn.text and game.num_rounds == MIN_ROUNDS:
        continue
      new_row.append(btn)
    if new_row:
      filtered.append(new_row)

  filtered.append([InlineKeyboardButton(b("perfect"), callback_data='s:rounds:done')])
  await edit_message(session, text, filtered)


async def render_choose_category_screen(session: Session, game: Game, user: User, start_idx = 0):
  text = t("choose_category", num_rounds=game.num_rounds)
  buttons = make_category_buttons(start_idx, user, game.all_categories, callback_prefix="s:cat", show_random=True)
  buttons.append([InlineKeyboardButton(text=b("random"), callback_data='s:cat:random')])
  buttons.append([InlineKeyboardButton(text=b("category_settings"), callback_data='e:categories')])
  await edit_message(session, text, buttons)


async def render_choose_mode_screen(session: Session, user: User, category_info = ""):
  text = t("choose_mode", category_info=category_info)
  buttons = [
    [InlineKeyboardButton(
      text=mode.label + (f" ({mode.min_players}{' R' if mode in user.random_modes else ''})"),
      callback_data=f's:mode:{mode.value}')
    ] for mode in GameMode if mode != GameMode.RANDOM
  ]
  buttons.append([InlineKeyboardButton(text=b("random_with_number", min_players_for_random=user.min_players_for_random), callback_data=f's:mode:{GameMode.RANDOM.value}')])
  buttons.append([InlineKeyboardButton(text=b("edit_random"), callback_data=f'e:modes')])
  await edit_message(session, text, buttons)


async def render_all_set_screen(session: Session, game: Game):
  text = t("all_set", mode_label=game.mode.label)
  buttons = [[InlineKeyboardButton(b("start_game"), callback_data='g:start_round')]]
  await edit_message(session, text, buttons)


# --- dispatch ---

async def handle_setup(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if session.game_substate is None and query and data:
    session.game_substate = SetupSubstate.PLAYERS_COUNT
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

      if game.type == "single" and not (len(player_names) == game.initial_players_count):
        await update.message.reply_text(t("min_players", initial_players_count=game.initial_players_count))
        return False
      elif game.type == "multiple" and not (1 <= len(player_names) <= slots):
        await update.message.reply_text(t("input_names_error", slots=slots))
        return False

      session.prepare_players(player_names, game)
      session.game_substate = SetupSubstate.WAITING

      if game.type == "multiple":
        players_names = ', '.join([p.name for p in session.players])
        text = t("names_confirmation_multiple", players_names=players_names, game_id=game.id, joined_players=len(game.players), initial_players_count=game.initial_players_count)

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, None, old_message=old_message, delete_old_message=True)

        if len(game.players) == game.initial_players_count:
          buttons = [[InlineKeyboardButton(text=b("continue"), callback_data='s:all_joined')]]
          owner_session = get_session_of_owner(game=game)
          await edit_message(owner_session, t("all_joined"), buttons)

          for cid in game.chat_ids:
            session = get_session_of_chat(cid)
            if session.game_substate == SetupSubstate.INPUT_NAMES:
              terminate_session(session)

        else:
          await broadcast_message(
            game=game, mode="edit",
            text=t("waiting_for_players", game_id=game.id, joined_players=len(game.players), initial_players_count=game.initial_players_count),
            exclude_chat_ids=[session.chat_id],
            only_with_substate=SetupSubstate.WAITING,
          )
          slots = empty_slots(game)
          await broadcast_message(
            game=game, mode="edit",
            text=t("input_names", slots=slots),
            exclude_chat_ids=[session.chat_id],
            only_with_substate=SetupSubstate.INPUT_NAMES,
          )

        return False

      elif game.type == "single":
        players_names = ', '.join([p.name for p in session.players])
        text = t("names_confirmation_single", players_names=players_names)
        buttons = [[InlineKeyboardButton(text=b("continue"), callback_data='s:all_joined')]]

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, buttons, old_message=old_message, delete_old_message=True)
        return False

  elif session.game_substate == SetupSubstate.WAITING:
    if query and data == "s:all_joined":
      await broadcast_message(game=game, mode="edit", text=t("waiting_for_game_creator"), exclude_chat_ids=[session.chat_id])

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
      user = get_user_by_id(update.effective_user.id)
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
      user = get_user_by_id(update.effective_user.id)
      game.all_categories = user.generated_categories + default_categories

      start_idx = 0
      if data.startswith("s:next_cats:"):
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(game.all_categories)-1))

      await render_choose_category_screen(session, game, user, start_idx)
      session.game_substate = SetupSubstate.CHOOSE_CATEGORY
      return False

    if data.startswith("s:cat:"):
      user = get_user_by_id(update.effective_user.id)

      category_idx = data.split(':')[2]
      if category_idx != "random":
        category = game.all_categories[int(category_idx)]
      else:
        game.random_category_options = user.random_categories
        category = None

      game.category = category
      title = "Random" if category is None else category.title
      category_info = t("category_info", category_title=title)

      await render_choose_mode_screen(session, user, category_info)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_MODE:
    if data == "e:modes":
      game.state = GameState.MODE_SETTINGS
      session.game_substate = None
      return True

    if data == "s:choose_mode":
      user = get_user_by_id(update.effective_user.id)
      category_info = t("category_info", category_title=game.category.title if game.category else "Random")
      await render_choose_mode_screen(session, user, category_info)
      session.game_substate = SetupSubstate.CHOOSE_MODE
      return False

    if data.startswith("s:mode:"):
      mode_txt = data.split(':')[2]
      mode = GameMode(mode_txt)

      if mode == GameMode.RANDOM:
        user = get_user_by_id(update.effective_user.id)
        if user.min_players_for_random > len(game.players):
          await query.answer(
            t("random_mode_min_players", min_players=user.min_players_for_random, current_players=len(game.players)),
            show_alert=True
          )
          return False

      if mode.min_players > len(game.players):
        await query.answer(
          t("mode_min_players", min_players=mode.min_players, current_players=len(game.players)),
          show_alert=True
        )
        return False

      if mode == GameMode.RANDOM:
        user = get_user_by_id(update.effective_user.id)
        game.random_mode_options = user.random_modes

      game.mode = mode
      await render_all_set_screen(session, game)
      session.game_substate = SetupSubstate.FINISHED
      return False

  elif session.game_substate == SetupSubstate.FINISHED:
    if data == "g:start_round":
      game.state = GameState.INFORM
      session.game_substate = None
      return True

  return False