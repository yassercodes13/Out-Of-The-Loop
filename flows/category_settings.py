from db.repositories.category_repo import add_category, delete_category
from flows.utils import *
from adapters.telegram.messaging import *
from flows.states import GameState
from flows.substates import CategorySettingsSubstate, SetupSubstate
from data.users import get_user_by_id, update_user
from handlers.utils import *
from data.default_categories import default_categories
from models.category import Category
from texts.refs import TextRef, Button
from config import CATEGORIES_PER_PAGE, MIN_LINES_FOR_CATEGORY, MIN_UNIQUE_WORDS


# --- screen renderers ---

async def render_category_settings_main_screen(session: Session, game: Game):
  text = TextRef("what_to_do")
  buttons = [
    [Button(TextRef("change_random_categories"), "e:toggle")],
    [Button(TextRef("create_category"), "e:create")],
    [Button(TextRef("delete_category"), "e:delete")],
    [Button(TextRef("view_category"), "e:view")],
  ]
  if game:
    buttons.append([Button(TextRef("back_to_category_selection"), "s:choose_category")])
  else:
    buttons.append([Button(TextRef("done"), "e:done")])
  await edit_message(session, text, buttons)


async def render_delete_list_screen_paged(session: Session, user: User, categories: list, start_idx: int):
  text = TextRef("select_category_to_delete")
  buttons = make_category_buttons(start_idx, user, categories, callback_prefix="e:delete")
  buttons.append([Button(TextRef("back_to_category_settings"), "e:categories")])
  await edit_message(session, text, buttons)


async def render_delete_confirm_screen(session: Session, category_title: str, idx: int):
  text = TextRef("confirm_delete", {"category_title": category_title})
  buttons = [
    [Button(TextRef("yes_delete"), f"e:delete_confirm:{idx}")],
    [Button(TextRef("no_keep"), "e:delete")]
  ]
  await edit_message(session, text, buttons)


async def render_deleted_screen(session: Session, category_title: str):
  text = TextRef("category_deleted", {"category_title": category_title})
  buttons = [
    [Button(TextRef("delete_another_category"), "e:delete")],
    [Button(TextRef("back_to_category_settings"), "e:categories")],
  ]
  await edit_message(session, text, buttons)


async def render_toggle_screen(session: Session, user: User, all_categories: list, start_idx: int = 0):
  text = TextRef("toggle_random_categories")
  buttons = make_category_buttons(start_idx, user, all_categories, show_marks=True, callback_prefix="e:toggle")
  buttons.append([Button(TextRef("done"), "e:categories")])
  await edit_message(session, text, buttons)


async def render_view_list_screen(session: Session, user: User, all_categories: list, start_idx: int = 0):
  text = TextRef("select_category_to_view")
  buttons = make_category_buttons(start_idx, user, all_categories, callback_prefix="e:view")
  buttons.append([Button(TextRef("back_to_category_settings"), "e:categories")])
  await edit_message(session, text, buttons)


async def render_view_category_screen(session: Session, category):
  words = "\n".join(category.words)
  text = TextRef("view_category_detail", {"title": category.title, "count": len(category.words), "words": words})
  buttons = [[Button(TextRef("back_to_view_categories"), "e:view")]]
  await edit_message(session, text, buttons)


async def render_create_screen(session: Session):
  text = TextRef("create_category_prompt")
  buttons = [[Button(TextRef("back_to_category_settings"), "e:categories")]]
  await edit_message(session, text, buttons)


async def render_created_screen(session: Session, title: str, word_count: int, old_message):
  text = TextRef("category_created", {"title": title, "word_count": word_count})
  buttons = [[Button(TextRef("back_to_category_settings"), "e:categories")]]
  await send_message(session, text, buttons, old_message=old_message, delete_old_message=True)


# --- dispatch ---

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
    await render_category_settings_main_screen(session, game)
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

      await render_delete_list_screen_paged(session, user, categories, start_idx)
      return False

    elif data.startswith("e:delete:"):
      idx = int(data.split(':')[2])
      if 0 <= idx < len(user.generated_categories):
        deleted_cat = user.generated_categories[idx]
        await render_delete_confirm_screen(session, deleted_cat.title, idx)
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
        
        await render_deleted_screen(session, deleted_cat.title)
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

    await render_toggle_screen(session, user, all_categories, start_idx)
    return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.VIEW] and data and (data.startswith("e:view") or data.startswith("e:next_cats:")):
    session.game_substate = CategorySettingsSubstate.VIEW

    if data == "e:view" or data.startswith("e:next_cats:"):
      start_idx = 0
      if "next_cats" in data:
        start_idx = int(data.split(':')[2])
        start_idx = max(0, min(start_idx, len(all_categories)-1))
      await render_view_list_screen(session, user, all_categories, start_idx)
      return False

    elif data.startswith("e:view:"):
      category_idx = int(data.split(':')[2])
      if 0 <= category_idx < len(all_categories):
        category = all_categories[category_idx]
        await render_view_category_screen(session, category)
      else:
        await query.answer()
        await send_popup_message(session, TextRef("invalid_category"), [[Button(TextRef("ok"), "i:ok")]], session)
      return False

  elif session.game_substate in [CategorySettingsSubstate.MAIN, CategorySettingsSubstate.CREATE] and data == "e:create":
    session.game_substate = CategorySettingsSubstate.CREATE
    await render_create_screen(session)
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

    old_message = update.message.reply_to_message if update.message else None
    await render_created_screen(session, title, len(words), old_message)
    return False

  return False


def make_category_buttons(start_idx: int, user: User, categories: list[Category], callback_prefix: str = "", show_random=False, show_marks=False):
  if show_random:
    buttons = [
      [Button(TextRef("text", {"text":f"{cat.title} (R)" if cat in user.random_categories else cat.title}), f"{callback_prefix}:{i}")]
      for i, cat in enumerate(categories) if start_idx <= i < CATEGORIES_PER_PAGE + start_idx
    ]
  elif show_marks:
    buttons = [
      [Button(TextRef("text", {"text": cat.title + (" ✔" if cat in user.random_categories else " ✘")}), f"{callback_prefix}:{i}")]
      for i, cat in enumerate(categories) if start_idx <= i < CATEGORIES_PER_PAGE + start_idx
    ]
  else:
    buttons = [
      [Button(TextRef("text", {"text": cat.title}), f"{callback_prefix}:{i}")]
      for i, cat in enumerate(categories) if start_idx <= i < CATEGORIES_PER_PAGE + start_idx
    ]

  nav_buttons = []
  prefix = callback_prefix.split(':')[0] + ":"
  if start_idx != 0:
    nav_buttons.append(Button(TextRef("prev_page"), f"{prefix}next_cats:{start_idx - CATEGORIES_PER_PAGE}"))
  if start_idx + CATEGORIES_PER_PAGE < len(categories):
    nav_buttons.append(Button(TextRef("next_page"), f"{prefix}next_cats:{start_idx + CATEGORIES_PER_PAGE}"))
  buttons.append(nav_buttons)

  return buttons