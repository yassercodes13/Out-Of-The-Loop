from flows.msg_utils import *
from flows.states import GameState
from flows.substates import CategorySettingsSubstate, SetupSubstate
from telegram import InlineKeyboardButton
from data.runtime_manager import *
from handlers.utils import *
from data.default_categories import default_categories
from models.category import Category

async def handle_category_settings(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = get_user_by_id(session.user_id)
  all_categories = user.generated_categories + default_categories

  if session.game_substate is None or data == "e:categories":
    session.game_substate = CategorySettingsSubstate.MAIN
  
  elif game and session.game_substate == CategorySettingsSubstate.MAIN and data == "s:choose_category":
    game.state = GameState.SETUP
    session.game_substate = SetupSubstate.CHOOSE_CATEGORY
    return True

# --- CATEGORY SETTINGS ---
  if session.game_substate == CategorySettingsSubstate.MAIN and data == "e:categories":
    text = "What do you want to do?"
    buttons = [
      [InlineKeyboardButton(text = "Change Random Categories", callback_data = "e:toggle")],
      [InlineKeyboardButton(text = "Create Category", callback_data = "e:create")],
      [InlineKeyboardButton(text = "Delete Category", callback_data = "e:delete")],
      [InlineKeyboardButton(text = "View Category", callback_data = "e:view")],
    ]
    
    if game:
      buttons.append([InlineKeyboardButton(text = "Back to category selection", callback_data = f"s:choose_category")])
    else:
      buttons.append([InlineKeyboardButton(text = "Done", callback_data = f"e:done")])

    await edit_message(session, text, buttons)
    return False
  
  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.DELETE] and data and (data.startswith("e:delete") or data.startswith("e:next_cats:")):
    
    session.game_substate = CategorySettingsSubstate.DELETE
    if data == "e:delete" or data.startswith("e:next_cats:"):
      categories = user.generated_categories
      if not categories:
        await update.callback_query.answer("You have no custom categories to delete.", show_alert=True)
        session.game_substate = CategorySettingsSubstate.MAIN
        return False
      
      start_idx = 0

      if query.data and query.data.startswith("e:next_cats:"):
        start_idx = int(query.data.split(':')[2])
        start_idx = max(0, min(start_idx, len(categories)-1))

      buttons = make_category_buttons(start_idx, user, categories, callback_prefix = "e:delete")
      buttons.append([InlineKeyboardButton(text = "Back to category settings", callback_data = "e:categories")])
      text = "Select a category to delete:"
      await edit_message(session, text, buttons)
      return False

    elif data and data.startswith("e:delete:"):
      idx = int(data.split(':')[2])
      
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories[idx]
        text = f"Sure you want to delete Category '{deleted_cat.title}'?"
      else:
        await update.callback_query.answer("Invalid category", show_alert=False)
      
      buttons = [
        [InlineKeyboardButton(text = "Yes, delete it", callback_data = f"e:delete_confirm:{idx}")],
        [InlineKeyboardButton(text = "No, keep it", callback_data = f"e:delete")]
      ]

      await edit_message(session, text, buttons)
      return False
    
    elif data and data.startswith("e:delete_confirm:"):
      idx = int(data.split(':')[2])      
      
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories.pop(idx)
        user.random_categories.remove(deleted_cat) if deleted_cat in user.random_categories else None
        all_categories = user.generated_categories + default_categories
        if len(user.random_categories) < 2:
          user.random_categories = [cat for cat in all_categories]

        text = f"Category '{deleted_cat.title}' deleted!"
      else:
        await update.callback_query.answer("Invalid category", show_alert=True)
        return False

      buttons = [
        [InlineKeyboardButton(text = "Delete another category", callback_data = "e:delete")],
        [InlineKeyboardButton(text = "Back to category settings", callback_data = "e:categories")],
      ]
      await edit_message(session, text, buttons)
      return False
  
  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.TOGGLE] and data and (data.startswith("e:toggle") or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.TOGGLE
    start_idx = 0
    
    if data.startswith("e:toggle:"):
      category_idx = int(data.split(':')[2])
      category = all_categories[category_idx]
      
      start_idx = category_idx - category_idx % 5

      if category not in user.random_categories:
        user.random_categories.append(category)
      elif category in user.random_categories and len(user.random_categories) > 2:
        user.random_categories.remove(category)
      else:
        await update.callback_query.answer("You must have at least 2 categories selected for random category option to be available.", show_alert=True)
        return False

    elif data.startswith("e:next_cats:"): 
      start_idx = int(query.data.split(':')[2])
      start_idx = max(0, min(start_idx, len(all_categories)-1))
    
    text = "Click a button to toggle if that category should be included in random category selection\n\nYou must have at least 2 categories selected for random category option to be available."
    buttons = make_category_buttons(start_idx, user, all_categories, show_marks = True, callback_prefix = "e:toggle")
    buttons.append([InlineKeyboardButton(text = "Done", callback_data = "e:categories")])

    await edit_message(session, text, buttons)
    return False
  
  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.VIEW] and data and (data.startswith("e:view")  or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.VIEW

    if data == "e:view" or data.startswith("e:next_cats:"):
      start_idx = 0
      if "next_cats" in data:
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(all_categories)-1))
      
      buttons = make_category_buttons(start_idx, user, all_categories, callback_prefix = "e:view")
      buttons.append([InlineKeyboardButton(text = "Back to category settings", callback_data = "e:categories")])
      text = "Select a category to view:"
      await edit_message(session, text, buttons)
      return False
    
    elif data.startswith("e:view:"):
      category_idx = int(data.split(':')[2])
      if 0 <= category_idx < len(all_categories):
        category = all_categories[category_idx]
        words = "\n".join(category.words)
        text = f"Category: {category.title}\n\nWords ({len(category.words)}):\n{words}"
        buttons = [[InlineKeyboardButton(text = "Back to view categories", callback_data = "e:view")]]
        await edit_message(session, text, buttons)
        return False
      else:
        await update.callback_query.answer("Invalid category", show_alert=True)
        return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.CREATE] and data == "e:create":
    session.game_substate = CategorySettingsSubstate.CREATE
    text = (
      "To add a custom category, reply to this message in the following format:\n\n"
      "Category Title\nWord1\nWord2\nWord3\n...\nWordN\n\n"
      "Number of words must be at least 13. Words should be unique."
    )
    buttons = [[InlineKeyboardButton(text = "Back to category settings", callback_data=f'e:categories')],]
    await edit_message(session, text, buttons)
    return False
  
  elif session.game_substate == CategorySettingsSubstate.CREATE and update.message and update.message.reply_to_message:
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

    user.generated_categories.append(new_category)
    user.random_categories.append(new_category) 

    text = f"Category '{title}' with {len(words)} words added!\n\nYou can create one more by replying again, or go back to category selection."
    buttons = [[InlineKeyboardButton(text = "Back to category settings", callback_data=f'e:categories')],]
    
    old_message = update.message.reply_to_message if update.message else None
    await send_message(session, text, buttons, old_message = old_message, delete_old_message = True)
      
    return False

 
def make_category_buttons(start_idx: int, user: User, categories: list[Category], callback_prefix: str = "", show_random = False, show_marks = False):
  
  if show_random:
    buttons = [
      [InlineKeyboardButton(text = f"{cat.title} (R)" if cat in user.random_categories else cat.title, callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if start_idx <= i < 5 + start_idx
    ]
  elif show_marks:
    buttons = [
      [InlineKeyboardButton(text = cat.title + (" ✔" if cat in user.random_categories else " ✘"), callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if start_idx <= i < 5 + start_idx
    ]
  else:
    buttons = [
      [InlineKeyboardButton(text = cat.title, callback_data = f"{callback_prefix}:{i}")] 
        for i,cat in enumerate(categories) if start_idx <= i < 5 + start_idx
    ]

  nav_buttons = []
  if start_idx != 0:
    nav_buttons.append(
      InlineKeyboardButton(text = "<<", callback_data = f"{callback_prefix[0:2]}next_cats:{start_idx - 5}")
    )
  if start_idx + 5 < len(categories):
    nav_buttons.append(
      InlineKeyboardButton(text = ">>", callback_data = f"{callback_prefix[0:2]}next_cats:{start_idx + 5}")
    )
  buttons.append(nav_buttons)

  return buttons
