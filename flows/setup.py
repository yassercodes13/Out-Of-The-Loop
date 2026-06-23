from flows.category_settings import make_category_buttons
from flows.msg_utils import *
from flows.states import GameState
from flows.substates import SetupSubstate
from telegram import CallbackQuery, InlineKeyboardButton
from data.runtime_manager import *
from handlers.utils import *
from data.default_categories import default_categories
from data.modes import GameMode
from config import BOT_USERNAME
from models.category import Category


# --- screen renderers ---

async def render_players_count_screen(session: Session):
  text = "Choose Number of players"
  buttons = [
    [
      InlineKeyboardButton(text=f"{i}", callback_data=f"s:players:{i}"),
      InlineKeyboardButton(text=f"{i+1}", callback_data=f"s:players:{i+1}")
    ] for i in range(3, 10, 2)
  ]
  await edit_message(session, text, buttons)

async def render_game_type_screen(session: Session):
  text = "How will you play?"
  buttons = [
    [InlineKeyboardButton(text="On the same phone", callback_data = "s:game_type:single")],
    [InlineKeyboardButton(text="On multiple phones", callback_data = "s:game_type:multiple")],
    [InlineKeyboardButton(text="How to play with multiple phones?", callback_data="s:game_type:help")]
  ]
  await edit_message(session, text, buttons)

async def render_choose_category_screen(session: Session, game: Game, user: User, start_idx = 0):
  text = f"Number of rounds set: {game.num_rounds}\n\nNow choose words category:"
  buttons = make_category_buttons(start_idx, user, game.all_categories, callback_prefix = "s:cat", show_random = True)
  buttons.append([InlineKeyboardButton(text = "🎲 Random", callback_data='s:cat:random')])
  buttons.append([InlineKeyboardButton(text = "⚙️ Category Settings", callback_data='e:categories')])
  await edit_message(session, text, buttons)

async def render_choose_mode_screen(session: Session, user: User, category_info = ""):
  text = f"{category_info}Now choose game mode:"
  buttons = [
    [InlineKeyboardButton(
      text = mode.label + (f" ({mode.min_players}{" R" if mode in user.random_modes else ""})"),
      callback_data=f's:mode:{mode.value}')
    ] for mode in GameMode if mode != GameMode.RANDOM
  ]
  buttons.append([InlineKeyboardButton(text = f"🎲 Random ({user.min_players_for_random})", callback_data=f's:mode:{GameMode.RANDOM.value}')])
  buttons.append([InlineKeyboardButton(text = "⚙️ Edit Random", callback_data=f'e:modes')])
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
        text = (
          "How to play on multiple phones?\n\n"
          "There are two main ways to play:\n\n"
          "• Same phone\n"
          "All players share one device and take turns.\n\n"
          "• Each player uses their own phone\n"
          "Everyone joins the same game using a code and plays on their own device.\n\n"
          "•• You can also mix both:\n"
          "For example, 5 players can play using 3 phones—some players share a device, others use their own.\n\n"
          "More phones = Less waiting time"
        )
        buttons = [[InlineKeyboardButton(text="Got it!", callback_data = "s:game_type:select")]]
        await edit_message(session, text, buttons)
        return False

      game.type = game_type
      session.game_substate = SetupSubstate.INPUT_NAMES

      if game.type == "single":
        text = (
          "Input players' names by replying to this message\n"
          "Names should be separated by spaces or each on a line.\n"
          f"Player count must be {game.initial_players_count}."
        )
        await edit_message(session, text)

      elif game.type == "multiple":
        slots = empty_slots(game)
        text = (
          "Share this game code with your friends so they can join:\n"
          f"{game.id}\n\n"
          "Or forawrd the next message to their chat\n\n"
          "Input players' names who will play on this phone (could be just your name) by replying to this message\n"
          "Names should be separated by spaces or each on a line.\n"
          f"game has room for {slots} players"
        )
        await edit_message(session, text)

        user = get_user_by_id(session.user_id)
        await session.bot.send_message(
          chat_id = session.chat_id,
          text = f"Join an out of the loop game by: {user.username}!",
          reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join", url = f"https://t.me/{BOT_USERNAME}?start={game.id}")]])
        )

      return False

  elif session.game_substate == SetupSubstate.INPUT_NAMES:
    if update.message and update.message.reply_to_message:
      # Players who join the game only work with the input names setup step
      player_names = update.message.text.split()
      slots = empty_slots(game)

      if game.type == "single" and not (len(player_names) == game.initial_players_count):
        await update.message.reply_text(f"You must have {game.initial_players_count} players.")
        return False
      elif game.type == "multiple" and not (1 <= len(player_names) <= slots):
        await update.message.reply_text(f"You must provide at least 1 player name and at most {slots}.")
        return False

      session.prepare_players(player_names, game)    # Create player objects and add to session and game
      session.game_substate = SetupSubstate.WAITING

      if game.type == "multiple":
        text = (
          f"Players names set: {', '.join([p.name for p in session.players])}\n"
          f"Now waiting for other players to join using the game code...\n\n"
          f"Game Code is {game.id}\n"
          f"Players joined: {len(game.players)}/{game.initial_players_count}"
        )

        buttons = None
        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, buttons, old_message = old_message, delete_old_message = True)

        if (len(game.players) == game.initial_players_count):
          buttons = [[InlineKeyboardButton(text="Continue", callback_data='s:all_joined')]]
          owner_session = get_session_of_owner(game = game)
          await edit_message(owner_session, "All players joined!", buttons)
          # Removing sessions that didn't add players when player count is full
          for cid in game.chat_ids:
            session = get_session_of_chat(cid)
            if session.game_substate == SetupSubstate.INPUT_NAMES:
              terminate_session(session)

        else:
          await broadcast_message(
            game = game, mode = "edit",
            text = (
              f"Now waiting for other players to join using the game code...\n\n"
              f"Game Code is {game.id}\n\n"
              f"Players joined: {len(game.players)}/{game.initial_players_count}"
            ),
            exclude_chat_ids = [session.chat_id],
            only_with_substate = SetupSubstate.WAITING,
            )
          slots = empty_slots(game)
          await broadcast_message(
            game = game, mode = "edit",
            text = (
              "Input players' names who will play on this phone (could be just your name) by replying to this message\n"
              "Names should be separated by spaces or each on a line.\n"
              f"game has room for {slots} players"
            ),
            exclude_chat_ids = [session.chat_id],
            only_with_substate = SetupSubstate.INPUT_NAMES,
            )

        return False

      elif game.type == "single":
        text = f"Players names set: {', '.join([p.name for p in session.players])}"
        buttons = [[InlineKeyboardButton(text="Continue", callback_data='s:all_joined')]]

        old_message = update.message.reply_to_message if update.message else None
        await send_message(session, text, buttons, old_message = old_message, delete_old_message = True)
        return False

  elif session.game_substate == SetupSubstate.WAITING:
    if query and data == "s:all_joined":  # Only game owner reaches this
      global_text = "All players joined\nWaiting for the game creator to finish setup."
      await broadcast_message(game = game, mode = "edit", text = global_text, exclude_chat_ids = [session.chat_id])

      game.num_rounds = len(game.players)   # Intialize the rounds count

      text = (
        "Now adjust number of rounds as you wish (1 to 25).\n"
        f"Current number of rounds: {game.num_rounds}"
      )

      buttons = [
        [
          InlineKeyboardButton("+1", callback_data='s:rounds:+1'),
          InlineKeyboardButton("-1", callback_data='s:rounds:-1'),
        ],
        [
          InlineKeyboardButton("+2", callback_data='s:rounds:+2'),
          InlineKeyboardButton("-2", callback_data='s:rounds:-2')
        ],
        [
          InlineKeyboardButton("+5", callback_data='s:rounds:+5'),
          InlineKeyboardButton("-5", callback_data='s:rounds:-5')
        ],
        [
          InlineKeyboardButton("+10", callback_data='s:rounds:+10'),
          InlineKeyboardButton("-10", callback_data='s:rounds:-10')
        ],
        [InlineKeyboardButton("Perfect!", callback_data='s:rounds:done')]
      ]

      await edit_message(session, text, buttons)
      session.game_substate = SetupSubstate.CHOOSE_ROUNDS
      return False

  elif session.game_substate == SetupSubstate.CHOOSE_ROUNDS:
    if data.startswith("s:rounds:") and data != "s:rounds:done":
      rounds_count = game.num_rounds
      rounds_count += int(data.split(':')[2])
      rounds_count = max(min(rounds_count, 25), 1)

      if game.num_rounds == rounds_count:  # Nothing to update
        return False

      game.num_rounds = rounds_count

      text = f"Current number of rounds: {game.num_rounds}"

      buttons = [
        [
          InlineKeyboardButton("+1", callback_data='s:rounds:+1'),
          InlineKeyboardButton("-1", callback_data='s:rounds:-1'),
        ],
        [
          InlineKeyboardButton("+2", callback_data='s:rounds:+2'),
          InlineKeyboardButton("-2", callback_data='s:rounds:-2')
        ],
        [
          InlineKeyboardButton("+5", callback_data='s:rounds:+5'),
          InlineKeyboardButton("-5", callback_data='s:rounds:-5')
        ],
        [
          InlineKeyboardButton("+10", callback_data='s:rounds:+10'),
          InlineKeyboardButton("-10", callback_data='s:rounds:-10')
        ],
      ]

      new_buttons = []
      for row in buttons:
        new_row = []
        for btn in row:
          if "+" in btn.text and rounds_count == 25:
            continue
          if "-" in btn.text and rounds_count == 1:
            continue
          new_row.append(btn)
        if new_row:
          new_buttons.append(new_row)

      new_buttons.append([InlineKeyboardButton("Perfect!", callback_data='s:rounds:done')])

      await edit_message(session, text, new_buttons)
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
      category_info = f"Words category set: {title}\n\n"

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
      category_info = f"Words category set: {game.category.title if game.category else 'Random'}\n\n"
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
            f"Random mode requires at least {user.min_players_for_random} players based on your current random mode settings.\nGame has {len(game.players)} players.",
            show_alert=True
          )
          return False

      if mode.min_players > len(game.players):
        await query.answer(
          f"This mode requires at least {mode.min_players} players. Game has {len(game.players)}",
          show_alert=True
        )
        return False

      if mode == GameMode.RANDOM:
        user = get_user_by_id(update.effective_user.id)
        game.random_mode_options = user.random_modes

      game.mode = mode
      text = f'Game mode set: {mode.label}\n\nAll set! Click below to start the game.'
      buttons = [
        [InlineKeyboardButton("Start Game", callback_data='g:start_round')]
      ]

      await edit_message(session, text, buttons)
      session.game_substate = SetupSubstate.FINISHED
      return False

  elif session.game_substate == SetupSubstate.FINISHED:
    if data == "g:start_round":
      game.state = GameState.INFORM
      session.game_substate = None
      return True

  return False