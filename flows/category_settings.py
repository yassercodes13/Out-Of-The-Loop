from db.repositories.category_repo import add_category, delete_category
from adapters.telegram.messaging import edit_message, send_popup_message, send_info_message, send_message
from flows.states import GameState
from flows.substates import CategorySettingsSubstate, SetupSubstate
from data.users import get_user_by_id, update_user
from telegram import Update
from data.default_categories import default_categories
from models.category import Category
from models import Game, Session
from texts.refs import TextRef, Button
from config import CATEGORIES_PER_PAGE, MIN_LINES_FOR_CATEGORY, MIN_UNIQUE_WORDS
from views.category_settings import (
  render_category_settings_main_screen,
  render_delete_list_screen_paged,
  render_delete_confirm_screen,
  render_deleted_screen,
  render_toggle_screen,
  render_view_list_screen,
  render_view_category_screen,
  render_create_screen,
  render_created_screen,
)

async def handle_category_settings(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  user = await get_user_by_id(session.user_id)
  all_categories = user.generated_categories + default_categories

  if session.game_substate is None or data == "e:categories":
    session.game_substate = CategorySettingsSubstate.MAIN

  elif game and session.game_substate == CategorySettingsSubstate.MAIN and data == "s:choose_category":
    game.state = GameState.SETUP
    session.game_substate = SetupSubstate.CHOOSE_CATEGORY
    await update_user(user)
    return True

  if session.game_substate == CategorySettingsSubstate.MAIN and data == "e:categories":
    show_back = (game is not None)
    screen = render_category_settings_main_screen(show_back)
    await edit_message(session, screen.textref, screen.buttons)
    await update_user(user)
    return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.DELETE] and data and (data.startswith("e:delete") or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.DELETE

    if data == "e:delete" or data.startswith("e:next_cats:"):
      categories = user.generated_categories
      if not categories:
        await query.answer()
        await send_popup_message(session, TextRef("no_custom_categories"), [[Button(TextRef("ok"), "i:ok")]], session)
        session.game_substate = CategorySettingsSubstate.MAIN
        return False

      start_idx = 0
      if data.startswith("e:next_cats:"):
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(categories)-1))

      screen = render_delete_list_screen_paged(categories, start_idx)
      await edit_message(session, screen.textref, screen.buttons)
      return False

    elif data.startswith("e:delete:"):
      idx = int(data.split(':')[2])
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories[idx]
        screen = render_delete_confirm_screen(deleted_cat.title, idx)
        await edit_message(session, screen.textref, screen.buttons)
      else:
        await query.answer()
        await send_info_message(
          session.bot,
          session.id,
          TextRef("invalid_category"),
          [[Button(TextRef("ok"), "i:ok")]],
          user.lang
        )
      return False

    elif data.startswith("e:delete_confirm:"):
      idx = int(data.split(':')[2])
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories.pop(idx)
        await delete_category(deleted_cat.id)
        if deleted_cat in user.random_categories:
          user.random_categories.remove(deleted_cat)
        await update_user(user)

        all_categories = user.generated_categories + default_categories
        if len(user.random_categories) < 2:
          user.random_categories = [cat for cat in all_categories]

        screen = render_deleted_screen(deleted_cat.title)
        await edit_message(session, screen.textref, screen.buttons)
      else:
        await query.answer()
        await send_popup_message(session, TextRef("invalid_category"), [[Button(TextRef("ok"), "i:ok")]], session)
      return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.TOGGLE] and data and (data.startswith("e:toggle") or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.TOGGLE
    start_idx = 0

    if data.startswith("e:toggle:"):
      category_idx = int(data.split(':')[2])
      category = all_categories[category_idx]
      start_idx = category_idx - (category_idx % CATEGORIES_PER_PAGE)

      if category not in user.random_categories:
        user.random_categories.append(category)
      elif len(user.random_categories) > 2:
        user.random_categories.remove(category)
      else:
        await query.answer()
        await send_popup_message(session, TextRef("min_two_categories"), [[Button(TextRef("ok"), "i:ok")]], session)
        return False

    elif data.startswith("e:next_cats:"):
      start_idx = int(data.split(':')[2])
      start_idx = max(0, min(start_idx, len(all_categories)-1))

    screen = render_toggle_screen(user, all_categories, start_idx)
    await edit_message(session, screen.textref, screen.buttons)
    return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.VIEW] and data and (data.startswith("e:view") or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.VIEW

    if data == "e:view" or data.startswith("e:next_cats:"):
      start_idx = 0
      if "next_cats" in data:
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(all_categories)-1))
      screen = render_view_list_screen(all_categories, start_idx)
      await edit_message(session, screen.textref, screen.buttons)
      return False

    elif data.startswith("e:view:"):
      category_idx = int(data.split(':')[2])
      if 0 <= category_idx < len(all_categories):
        category = all_categories[category_idx]
        screen = render_view_category_screen(category)
        await edit_message(session, screen.textref, screen.buttons)
      else:
        await query.answer()
        await send_popup_message(session, TextRef("invalid_category"), [[Button(TextRef("ok"), "i:ok")]], session)
      return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.CREATE] and data == "e:create":
    session.game_substate = CategorySettingsSubstate.CREATE
    screen = render_create_screen()
    await edit_message(session, screen.textref, screen.buttons)
    return False

  elif session.game_substate == CategorySettingsSubstate.CREATE and update.message and update.message.reply_to_message:
    lines = update.message.text.splitlines()
    if len(lines) < MIN_LINES_FOR_CATEGORY:
      await query.answer()
      await send_popup_message(session, TextRef("create_too_few_lines"), [[Button(TextRef("ok"), "i:ok")]], session)
      return False

    title = lines[0].capitalize()
    words = list(dict.fromkeys(w for w in lines[1:] if w.strip()))
    if len(words) < MIN_UNIQUE_WORDS:
      await query.answer()
      await send_popup_message(session, TextRef("create_too_few_words"), [[Button(TextRef("ok"), "i:ok")]], session)
      return False

    new_category = Category(title=title, words=words, owner_id=update.effective_user.id)
    user.generated_categories.append(new_category)
    user.random_categories.append(new_category)
    await add_category(new_category)
    await update_user(user)

    screen = render_created_screen(title, len(words))
    old_message = update.message.reply_to_message if update.message else None
    await send_message(session, screen.textref, screen.buttons, old_message=old_message, delete_old_message=True)
    return False

  return False