from views.category_settings import make_category_buttons
from models import Game, User
from models.modes import GameMode
from config import MAX_ROUNDS, MIN_ROUNDS, PLAYER_COUNT_OPTIONS_PER_ROW, ROUND_ADJUST_STEPS, MAX_PLAYERS, MIN_PLAYERS
from texts.refs import TextRef, Button, Screen


def render_players_count_screen() -> Screen:
  text = TextRef("choose_number_of_players")
  buttons = [
    [
      Button(TextRef("text", {"text": f"{i}"}), f"s:players:{i}"),
      Button(TextRef("text", {"text": f"{i+1}"}), f"s:players:{i+1}")
    ] for i in range(MIN_PLAYERS, MAX_PLAYERS, PLAYER_COUNT_OPTIONS_PER_ROW)
  ]
  return Screen(textref=text, buttons=buttons)


def render_game_type_screen() -> Screen:
  text = TextRef("choose_game_type")
  buttons = [
    [Button(TextRef("same_phone"), "s:game_type:single")],
    [Button(TextRef("multiple_phones"), "s:game_type:multiple")],
    [Button(TextRef("multiple_phones_help"), "s:game_type:help")]
  ]
  return Screen(textref=text, buttons=buttons)


def render_game_type_help_screen() -> Screen:
  text = TextRef("game_type_help")
  buttons = [[Button(TextRef("got_it"), "s:game_type:select")]]
  return Screen(textref=text, buttons=buttons)


def render_input_names_single_screen(initial_players_count: int) -> Screen:
  text = TextRef("game_type_single", {"initial_players_count": initial_players_count})
  return Screen(textref=text)


def render_input_names_multiple_screen(game_id: int, slots: int) -> Screen:
  text = TextRef("game_type_multiple", {"game_id": game_id, "slots": slots})
  return Screen(textref=text)


def render_adjust_rounds_screen(num_rounds: int, initial: bool = False) -> Screen:
  text = TextRef("adjust_number_of_rounds" if initial else "current_number_of_rounds", {"num_rounds": num_rounds})

  buttons = []
  for step in ROUND_ADJUST_STEPS:
    row = []
    if num_rounds + step <= MAX_ROUNDS:
      row.append(Button(TextRef("text", {"text": f"+{step}"}), f's:rounds:+{step}'))
    if num_rounds - step >= MIN_ROUNDS:
      row.append(Button(TextRef("text", {"text": f"-{step}"}), f's:rounds:-{step}'))
    if row:
      buttons.append(row)

  buttons.append([Button(TextRef("perfect"), 's:rounds:done')])
  return Screen(textref=text, buttons=buttons)


def render_choose_category_screen(game: Game, user: User, start_idx: int = 0) -> Screen:
  text = TextRef("choose_category", {"num_rounds": game.num_rounds})
  buttons = make_category_buttons(
    start_idx,
    game.all_categories,
    "s:cat",                
    user.random_categories, 
    True                    
  )
  buttons.append([Button(TextRef("random"), 's:cat:random')])
  buttons.append([Button(TextRef("category_settings"), 'e:categories')])
  return Screen(textref=text, buttons=buttons)


def render_choose_mode_screen(user: User, category_info: str = "", mode_change: bool = False) -> Screen:
  if category_info != "":
    text = TextRef("choose_mode", {"category_info": category_info})
  elif mode_change:
    text = TextRef("mode_change_needed")
  else:
    text = None

  buttons = [
    [Button(TextRef("text", {"text": mode.label + f" ({mode.min_players}{' R' if mode in user.random_modes else ''})"}), f's:mode:{mode.name}')]
    for mode in GameMode if mode != GameMode.RANDOM
  ]
  buttons.append([Button(TextRef("random_with_number", {"min_players_for_random": user.min_players_for_random}), f's:mode:{GameMode.RANDOM.name}')])
  buttons.append([Button(TextRef("edit_random"), 'e:modes')])
  return Screen(textref=text, buttons=buttons)


def render_all_set_screen(mode_label: str) -> Screen:
  text = TextRef("all_set", {"mode_label": mode_label})
  buttons = [[Button(TextRef("start_game"), 'g:start_round')]]
  return Screen(textref=text, buttons=buttons)


def render_min_players_popup(initial_players_count: int) -> Screen:
  text = TextRef("min_players", {"initial_players_count": initial_players_count})
  return Screen(textref=text, buttons=[[Button(TextRef("ok"), "i:ok")]])


def render_input_names_error_popup(slots: int) -> Screen:
  text = TextRef("input_names_error", {"slots": slots})
  return Screen(textref=text, buttons=[[Button(TextRef("ok"), "i:ok")]])


def render_random_mode_min_players_popup(min_players: int, current_players: int) -> Screen:
  text = TextRef("random_mode_min_players", {"min_players": min_players, "current_players": current_players})
  return Screen(textref=text, buttons=[[Button(TextRef("ok"), "i:ok")]])


def render_mode_min_players_popup(min_players: int, current_players: int) -> Screen:
  text = TextRef("mode_min_players", {"min_players": min_players, "current_players": current_players})
  return Screen(textref=text, buttons=[[Button(TextRef("ok"), "i:ok")]])


def render_names_confirmation_multiple_screen(players_names: str, game_id: int, joined_players: int, initial_players_count: int) -> Screen:
  text = TextRef("names_confirmation_multiple", {
    "players_names": players_names, "game_id": game_id,
    "joined_players": joined_players, "initial_players_count": initial_players_count
  })
  return Screen(textref=text)


def render_all_joined_screen() -> Screen:
  text = TextRef("all_joined")
  buttons = [[Button(TextRef("continue"), 's:all_joined')]]
  return Screen(textref=text, buttons=buttons)


def render_waiting_for_players_screen(game_id: int, joined_players: int, initial_players_count: int) -> Screen:
  text = TextRef("waiting_for_players", {
    "game_id": game_id, "joined_players": joined_players, "initial_players_count": initial_players_count
  })
  return Screen(textref=text)


def render_input_names_broadcast_screen(slots: int) -> Screen:
  text = TextRef("input_names", {"slots": slots})
  return Screen(textref=text)


def render_names_confirmation_single_screen(players_names: str) -> Screen:
  text = TextRef("names_confirmation_single", {"players_names": players_names})
  buttons = [[Button(TextRef("continue"), 's:all_joined')]]
  return Screen(textref=text, buttons=buttons)


def render_waiting_for_game_creator_screen() -> Screen:
  return Screen(textref=TextRef("waiting_for_game_creator"))