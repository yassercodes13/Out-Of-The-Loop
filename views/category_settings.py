from texts.refs import TextRef, Button, Screen
from models.user import User
from models.category import Category
from config import CATEGORIES_PER_PAGE

def make_category_buttons(
  start_idx: int,
  categories: list[Category],
  callback_prefix: str,
  random_categories: list[Category] = None,
  show_marks: bool = False
) -> list[list[Button]]:
  """
  Builds a paginated list of category buttons.
  - callback_prefix: e.g., "e:delete", "e:toggle", "e:view"
  - If show_marks is True, shows a checkmark if category is in random_categories.
  - If random_categories is provided and show_marks is True, marks are shown.
  """
  buttons = []
  end = min(start_idx + CATEGORIES_PER_PAGE, len(categories))

  for i in range(start_idx, end):
    cat = categories[i]
    label = cat.title
    if show_marks and random_categories is not None:
      label += " ✔" if cat in random_categories else " ✘"
    buttons.append([Button(TextRef("text", {"text": label}), f"{callback_prefix}:{i}")])

  nav_buttons = []
  prefix = callback_prefix.split(':')[0] + ":"
  if start_idx > 0:
    nav_buttons.append(Button(TextRef("prev_page"), f"{prefix}next_cats:{start_idx - CATEGORIES_PER_PAGE}"))
  if end < len(categories):
    nav_buttons.append(Button(TextRef("next_page"), f"{prefix}next_cats:{end}"))
  if nav_buttons:
    buttons.append(nav_buttons)

  return buttons

def render_category_settings_main_screen(show_back_to_game: bool) -> Screen:
  """Main category settings menu."""
  text = TextRef("what_to_do")
  buttons = [
    [Button(TextRef("change_random_categories"), "e:toggle")],
    [Button(TextRef("create_category"), "e:create")],
    [Button(TextRef("delete_category"), "e:delete")],
    [Button(TextRef("view_category"), "e:view")],
  ]
  if show_back_to_game:
    buttons.append([Button(TextRef("back_to_category_selection"), "s:choose_category")])
  else:
    buttons.append([Button(TextRef("done"), "e:done")])
  return Screen(textref=text, buttons=buttons)


def render_delete_list_screen_paged(
  categories: list[Category],
  start_idx: int
) -> Screen:
  """List of custom categories to delete, with pagination."""
  text = TextRef("select_category_to_delete")
  buttons = make_category_buttons(start_idx, categories, "e:delete")
  buttons.append([Button(TextRef("back_to_category_settings"), "e:categories")])
  return Screen(textref=text, buttons=buttons)


def render_delete_confirm_screen(category_title: str, idx: int) -> Screen:
  """Confirm deletion of a category."""
  text = TextRef("confirm_delete", {"category_title": category_title})
  buttons = [
    [Button(TextRef("yes_delete"), f"e:delete_confirm:{idx}")],
    [Button(TextRef("no_keep"), "e:delete")]
  ]
  return Screen(textref=text, buttons=buttons)


def render_deleted_screen(category_title: str) -> Screen:
  """Category deleted confirmation."""
  text = TextRef("category_deleted", {"category_title": category_title})
  buttons = [
    [Button(TextRef("delete_another_category"), "e:delete")],
    [Button(TextRef("back_to_category_settings"), "e:categories")],
  ]
  return Screen(textref=text, buttons=buttons)


def render_toggle_screen(
  user: User,
  all_categories: list[Category],
  start_idx: int = 0
) -> Screen:
  """Toggle random categories inclusion."""
  text = TextRef("toggle_random_categories")
  buttons = make_category_buttons(
    start_idx,
    all_categories,
    "e:toggle",
    random_categories=user.random_categories,
    show_marks=True
  )
  buttons.append([Button(TextRef("done"), "e:categories")])
  return Screen(textref=text, buttons=buttons)


def render_view_list_screen(
  all_categories: list[Category],
  start_idx: int = 0
) -> Screen:
  """List categories to view."""
  text = TextRef("select_category_to_view")
  buttons = make_category_buttons(start_idx, all_categories, "e:view")
  buttons.append([Button(TextRef("back_to_category_settings"), "e:categories")])
  return Screen(textref=text, buttons=buttons)


def render_view_category_screen(category: Category) -> Screen:
  """Show category details (title and word list)."""
  words = "\n".join(category.words)
  text = TextRef("view_category_detail", {
    "title": category.title,
    "count": len(category.words),
    "words": words
  })
  buttons = [[Button(TextRef("back_to_view_categories"), "e:view")]]
  return Screen(textref=text, buttons=buttons)


def render_create_screen() -> Screen:
  """Prompt to create a new category."""
  text = TextRef("create_category_prompt")
  buttons = [[Button(TextRef("back_to_category_settings"), "e:categories")]]
  return Screen(textref=text, buttons=buttons)


def render_created_screen(title: str, word_count: int) -> Screen:
  """Category created confirmation."""
  text = TextRef("category_created", {"title": title, "word_count": word_count})
  buttons = [[Button(TextRef("back_to_category_settings"), "e:categories")]]
  return Screen(textref=text, buttons=buttons)