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


async def handle_setup(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if session.game_substate is None and query and query.data:
    session.game_substate = SetupSubstate.PLAYERS_COUNT
    
    text = "Choose Number of players"
    buttons = [
      [
        InlineKeyboardButton(text=f"{i}", callback_data=f"s:players:{i}"),
        InlineKeyboardButton(text=f"{i+1}", callback_data=f"s:players:{i+1}")
      ] for i in range(3,10,2) 
    ]

    await edit_message(session, text, buttons)
    return False

  if (session.game_substate == SetupSubstate.PLAYERS_COUNT and query.data.startswith("s:players:")) or (session.game_substate == SetupSubstate.GAME_TYPE and query.data.startswith("s:game_type:select")):

    if session.game_substate == SetupSubstate.PLAYERS_COUNT:
      players_count = int(query.data.split(":")[2])
      game.intial_players_count = players_count

    text = "How will you play?"
    buttons = [
      [InlineKeyboardButton(text="On the same phone", callback_data = "s:game_type:single")],
      [InlineKeyboardButton(text="On multiple phones", callback_data = "s:game_type:multiple")],
      [InlineKeyboardButton(text="How to play with multiple phones?", callback_data="s:game_type:help")]
    ]
    session.game_substate = SetupSubstate.GAME_TYPE
    await edit_message(session, text, buttons)
    return False

  # --- initialize setup ---
  if session.game_substate == SetupSubstate.GAME_TYPE and query.data.startswith("s:game_type:"):
    game_type = query.data.split(":")[2]
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
    else:
      game.type = game_type
      session.game_substate = SetupSubstate.INPUT_NAMES
    
    if game.type == "single":
      text = (
        "Input players' names by replying to this message\n"
        "Names should be separated by spaces or each on a line.\n"
        f"Player count must be {game.intial_players_count}."
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

  # --- INPUT_NAMES: expecting a text reply ---
  if session.game_substate == SetupSubstate.INPUT_NAMES and update.message.reply_to_message:   
    # Players who join the game only work with the input names setup step
    
    player_names = update.message.text.split()
    slots = empty_slots(game)

    if game.type == "single" and not (len(player_names) == game.intial_players_count):
      await update.message.reply_text(f"You must have {game.intial_players_count} players.")
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
        f"Players joined: {len(game.players)}/{game.intial_players_count}"
      )

      buttons = None 
      old_message = update.message.reply_to_message if update.message else None
      await send_message(session, text, buttons, old_message = old_message, delete_old_message = True)
      
      if (len(game.players) == game.intial_players_count):
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
            f"Players joined: {len(game.players)}/{game.intial_players_count}"
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
  
  if session.game_substate == SetupSubstate.WAITING and query and data == "s:all_joined": #Only game owner reaches this
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


  # --- CHOOSE_ROUNDS ---
  if session.game_substate == SetupSubstate.CHOOSE_ROUNDS and query.data.startswith("s:rounds:") and query.data != "s:rounds:done":
    rounds_count = game.num_rounds
    rounds_count += int(query.data.split(':')[2])
    rounds_count = max(min(rounds_count, 25), 1)
    
    if game.num_rounds == rounds_count: # Nothing to update
      return False
    
    game.num_rounds = rounds_count

    text = (
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

  # --- CHOOSE CATEGORY ---
  if (session.game_substate == SetupSubstate.CHOOSE_ROUNDS and data == ("s:rounds:done")) or (session.game_substate == SetupSubstate.CATEGORY_SETTINGS and data == "s:choose_category") or (session.game_substate == SetupSubstate.CHOOSE_CATEGORY and data and data.startswith("s:next_cats:")):

    user = get_user_by_id(update.effective_user.id)
    game.all_categories = user.generated_categories + default_categories 
    text = f"Number of rounds set: {game.num_rounds}\n\nNow choose words category:"
    
    cat_start_idx = 0

    if query.data and query.data.startswith("s:next_cats:"):
      cat_start_idx = int(query.data.split(':')[2])
      cat_start_idx = max(0, min(cat_start_idx, len(game.all_categories)-1))

    buttons = category_buttons(cat_start_idx, user, game.all_categories, callback_prefix = "s:cat", show_random = True)
    buttons.append([InlineKeyboardButton(text = "🎲 Random", callback_data='s:cat:random')])
    buttons.append([InlineKeyboardButton(text = "⚙️ Category Settings", callback_data='s:cat_settings')])

    
    await edit_message(session, text, buttons)
    session.game_substate = SetupSubstate.CHOOSE_CATEGORY
    return False

  # --- CATEGORY SETTINGS ---
  if session.game_substate in [SetupSubstate.CATEGORY_SETTINGS, SetupSubstate.CREATE_CATEGORY, SetupSubstate.CHOOSE_CATEGORY] and data and data.startswith("s:cat_"):
  
    session.game_substate = SetupSubstate.CATEGORY_SETTINGS
    user = get_user_by_id(session.user_id)

    if data == "s:cat_settings":
      text = "What do you want to do?"
      buttons = [
        [InlineKeyboardButton(text = "Edit Random Categories", callback_data = "s:cat_edit_random")],
        [InlineKeyboardButton(text = "Create Category", callback_data = "s:create_category")],
        [InlineKeyboardButton(text = "Delete Category", callback_data = "s:cat_delete")],
        [InlineKeyboardButton(text = "View Category", callback_data = "s:cat_view")],
        [InlineKeyboardButton(text = "Back to category selection", callback_data = f"s:choose_category")]
      ]

      await edit_message(session, text, buttons)
      return False
    elif data == "s:cat_delete" or data.startswith("s:cat_delete_next_cats:"):
      
      categories = user.generated_categories
      if not categories:
        await update.callback_query.answer("You have no custom categories to delete.", show_alert=True)
        return False
      
      cat_start_idx = 0

      if query.data and query.data.startswith("s:cat_delete_next_cats:"):
        cat_start_idx = int(query.data.split(':')[2])
        cat_start_idx = max(0, min(cat_start_idx, len(categories)-1))

      buttons = category_buttons(cat_start_idx, user, categories, extra_prefix = "cat_delete_", callback_prefix = "s:cat_delete")
      buttons.append([InlineKeyboardButton(text = "Back to category settings", callback_data = "s:cat_settings")])
      text = "Select a category to delete:"
      await edit_message(session, text, buttons)
      return False

    elif data and data.startswith("s:cat_delete:"):
      idx = int(data.split(':')[2])
      
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories[idx]
        text = f"Sure you want to delete Category '{deleted_cat.title}'?"
      else:
        await update.callback_query.answer("Invalid category", show_alert=True)
      
      buttons = [
        [InlineKeyboardButton(text = "Yes, delete it", callback_data = f"s:cat_delete_confirm:{idx}")],
        [InlineKeyboardButton(text = "No, keep it", callback_data = f"s:cat_settings")]
      ]

      await edit_message(session, text, buttons)
      return False
    
    elif data and data.startswith("s:cat_delete_confirm:"):
      idx = int(data.split(':')[2])      
      
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories.pop(idx)
        user.random_categories.pop(idx) if deleted_cat in user.random_categories else None
        text = f"Category '{deleted_cat.title}' deleted!"
      else:
        await update.callback_query.answer("Invalid category", show_alert=True)
        return False

      buttons = [
        [InlineKeyboardButton(text = "Delete another category", callback_data = "s:cat_delete")],
        [InlineKeyboardButton(text = "Back to category settings", callback_data = "s:cat_settings")],
        [InlineKeyboardButton(text = "Back to category selection", callback_data = f"s:choose_category")],
      ]
      await edit_message(session, text, buttons)
      return False
    
    elif data == "s:cat_edit_random" or (data and data.startswith("s:cat_toggle")):
    
      cat_start_idx = 0

      if data.startswith("s:cat_toggle:"):
        category_idx = int(data.split(':')[2])
        category = game.all_categories[category_idx]
        if category not in user.random_categories:
          user.random_categories.append(category)
        elif category in user.random_categories and len(user.random_categories) > 2:
          user.random_categories.remove(category)
        else:
          await update.callback_query.answer("You must have at least 2 categories selected for random category option to be available.", show_alert=True)
          return False

      elif data.startswith("s:cat_toggle_next_cats:"): 
        cat_start_idx = int(query.data.split(':')[2])
        cat_start_idx = max(0, min(cat_start_idx, len(game.all_categories)-1))
      
      text = "Click a button to toggle if that category should be included in random category selection\n\nYou must have at least 2 categories selected for random category option to be available"
      buttons = category_buttons(cat_start_idx, user, game.all_categories, show_marks = True, extra_prefix = "cat_toggle_", callback_prefix = "s:cat_toggle")
      buttons.append([InlineKeyboardButton(text = "Done", callback_data = "s:cat_settings")])

      await edit_message(session, text, buttons)
      return False
    
    elif data.startswith("s:cat_view"):
      if data.startswith("s:cat_view") and not data.startswith("s:cat_view:"):
        cat_start_idx = 0
        if "next_cats" in data:
          cat_start_idx = int(data.split(':')[2])
          cat_start_idx = max(0, min(cat_start_idx, len(game.all_categories)-1))
        
        buttons = category_buttons(cat_start_idx, user, game.all_categories, extra_prefix = "cat_view_", callback_prefix = "s:cat_view")
        buttons.append([InlineKeyboardButton(text = "Back to category settings", callback_data = "s:cat_settings")])
        text = "Select a category to view:"
        await edit_message(session, text, buttons)
        return False
      else:
        category_idx = int(data.split(':')[2])
        if 0 <= category_idx < len(game.all_categories):
          category = game.all_categories[category_idx]
          words = "\n".join(category.words)
          text = f"Category: {category.title}\n\nWords ({len(category.words)}):\n{words}"
          buttons = [[InlineKeyboardButton(text = "Back to view categories", callback_data = "s:cat_view")]]
          await edit_message(session, text, buttons)
          return False
        else:
          await update.callback_query.answer("Invalid category", show_alert=True)
          return False


  # --- ADD CATEGORY ---
  if session.game_substate == SetupSubstate.CATEGORY_SETTINGS and data == "s:create_category":
    session.game_substate = SetupSubstate.CREATE_CATEGORY
    text = (
      "To add a custom category, reply to this message in the following format:\n\n"
      "Category Title\nWord1\nWord2\nWord3\n...\nWordN\n\n"
      "Number of words must be at least 13. Words should be unique."
    )
    buttons = [[InlineKeyboardButton(text = "Back to category settings", callback_data=f's:cat_settings')],]
    await edit_message(session, text, buttons)
    return False
  
  # --- CONFIRM ADDED CATEGORY ---
  if session.game_substate == SetupSubstate.CREATE_CATEGORY and update.message and update.message.reply_to_message:
    lines = update.message.text.splitlines()
    if len(lines) < 14:
      await update.message.reply_text("You must provide at least a title and 13 words. remember duplicates gets removed.")
      return False
    
    title = lines[0].capitalize()
    words = list(dict.fromkeys(w for w in lines[1:] if w.strip())) # Remove duplicates
    if len(words) < 13:
      await update.message.reply_text("You must provide at least 13 unique words.")
      return False
    
    new_category = Category(title=title, words=words, owner_id=update.effective_user.id)
    new_category.generate_id()  # Generate a unique ID for the category
    user = get_user_by_id(update.effective_user.id)
    user.generated_categories.append(new_category)
    user.random_categories.append(new_category)
    game.all_categories = user.generated_categories + default_categories # Update game's categories list to include the new category 

    text = f"Category '{title}' with {len(words)} words added!\n\nYou can create one more by replying again, or go back to category selection."
    buttons = [[InlineKeyboardButton(text = "Back to category settings", callback_data=f's:cat_settings')],]
    
    old_message = update.message.reply_to_message if update.message else None
    await send_message(session, text, buttons, old_message = old_message, delete_old_message = True)
      
    return False

  # --- CHOOSE_CATEGORY ---
  if (session.game_substate == SetupSubstate.CHOOSE_CATEGORY and query.data.startswith("s:cat:")) or (session.game_substate == SetupSubstate.EDIT_RANDOM_MODE and query.data.startswith("s:choose_mode")):
    
    user = get_user_by_id(update.effective_user.id)

    # If coming from edit_random_mode, don't update category, just go to mode selection
    category_info = ""
    if query.data.startswith("s:cat:"):
      category_idx = query.data.split(':')[2]
      if category_idx != "random":
        category = game.all_categories[int(category_idx)]
      else:
        game.random_category_options = user.random_categories
        category = None

      game.category = category
      title = "Random" if category is None else category.title
      category_info = f"Words category set: {title}\n\n"

    # Mode selection
    text = f"{category_info}Now choose game mode:"
    buttons = [
      [InlineKeyboardButton(
        text = mode.label + (f" ({mode.min_players}{" R" if mode in user.random_modes else ""})"),
        callback_data=f's:mode:{mode.value}')
      ] for mode in GameMode if mode != GameMode.RANDOM
    ]
    buttons.append([InlineKeyboardButton(text = f"🎲 Random ({user.least_random})", callback_data=f's:mode:{GameMode.RANDOM.value}')])
    buttons.append([InlineKeyboardButton(text = "⚙️ Edit Random", callback_data=f's:edit_random')])

    await edit_message(session, text, buttons)
    session.game_substate = SetupSubstate.CHOOSE_MODE
    return False

  # --- EDIT_RANDOM_MODE ---
  if (session.game_substate == SetupSubstate.CHOOSE_MODE and data == "s:edit_random") or (session.game_substate == SetupSubstate.EDIT_RANDOM_MODE and query.data.startswith("s:toggle_random:")):
    session.game_substate = SetupSubstate.EDIT_RANDOM_MODE
    user = get_user_by_id(update.effective_user.id)

    if query.data.startswith("s:toggle_random:"):
      mode_txt = query.data.split(':')[2]
      mode = GameMode(mode_txt)

      if mode in user.random_modes:
        if len(user.random_modes) <= 2:
          await query.answer("You must have at least 2 modes selected for random mode.", show_alert=True)
          return False
        user.random_modes.remove(mode)
      else:
        user.random_modes.append(mode)
      user.set_least_random() # Update least_random based on current random_modes

    text = (
      "The modes you select here will be the only ones that show up when you choose random mode.\n"
      "You have to select at least 2 modes\n\n"
      f"To play with the current list of modes you must have at least {user.least_random} players."
    )

    buttons = [
      [InlineKeyboardButton(
        text = mode.label + (" ✔" if mode in user.random_modes else " ✘"),
        callback_data=f's:toggle_random:{mode.value}'
      )] for mode in GameMode if mode != GameMode.RANDOM
    ]
    buttons.append([InlineKeyboardButton(text = "Back to mode selection", callback_data=f's:choose_mode')])

    await edit_message(session, text, buttons)
    return False

  # --- CHOOSE_MODE ---
  if session.game_substate == SetupSubstate.CHOOSE_MODE and query.data.startswith("s:mode:"):
    mode_txt = query.data.split(':')[2]
    mode = GameMode(mode_txt)

    # validate min players
    if mode == GameMode.RANDOM:
      user = get_user_by_id(update.effective_user.id)
      if user.least_random > len(game.players):
        await query.answer(
          f"Random mode requires at least {user.least_random} players based on your current random mode settings.\nGame has {len(game.players)} players.",
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
    text=f'Game mode set: {mode.label}\n\nAll set! Click below to start the game.'
    buttons = [
      [InlineKeyboardButton("Start Game", callback_data='g:start_round')]
    ]
    
    await edit_message(session, text, buttons)
    session.game_substate = SetupSubstate.FINISHED
    return False

  if session.game_substate == SetupSubstate.FINISHED and data == "g:start_round":
    game.state = GameState.INFORM
    session.game_substate = None
    return True
  
  return False

def category_buttons(cat_start_idx: int, user: User, categories: list[Category], callback_prefix: str = "", extra_prefix: str = "", show_random = False, show_marks = False):
  
  if show_random:
    buttons = [
      [InlineKeyboardButton(text = f"{cat.title} (R)" if cat in user.random_categories else cat.title, callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if cat_start_idx <= i < 5 + cat_start_idx
    ]
  elif show_marks:
    buttons = [
      [InlineKeyboardButton(text = cat.title + (" ✔" if cat in user.random_categories else " ✘"), callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if cat_start_idx <= i < 5 + cat_start_idx
    ]
  else:
    buttons = [
      [InlineKeyboardButton(text = cat.title, callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if cat_start_idx <= i < 5 + cat_start_idx
    ]

  nav_buttons = []
  if cat_start_idx != 0:
    nav_buttons.append(
      InlineKeyboardButton(text = "<<", callback_data = f"s:{extra_prefix}next_cats:{cat_start_idx - 5}")
    )
  if cat_start_idx + 5 < len(categories):
    nav_buttons.append(
      InlineKeyboardButton(text = ">>", callback_data = f"s:{extra_prefix}next_cats:{cat_start_idx + 5}")
    )
  buttons.append(nav_buttons)

  return buttons
