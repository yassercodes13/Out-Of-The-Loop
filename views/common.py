from config import BOT_USERNAME
from texts.refs import TextRef, Button, Screen


# --- start_bot / start_new_game ---

def render_welcome_screen() -> Screen:
  buttons = [
    [Button(TextRef("start_game"), 's:setup_game')],
    [Button(TextRef("view_game_rules"), 'help')],
  ]
  return Screen(textref=TextRef("welcome"), buttons=buttons)


def render_starting_new_game_warning_screen() -> Screen:
  buttons = [
    [Button(TextRef("start_it"), 's:setup_game')],
    [Button(TextRef("dont_start"), 'del_message')],
  ]
  return Screen(textref=TextRef("starting_new_game_warning"), buttons=buttons)


# --- join_game ---

def render_join_usage_screen(already_in_game: bool) -> Screen:
  text = [TextRef("join_usage")]
  if already_in_game:
    text = [TextRef("already_in_game_join_warning")] + text
  return Screen(textref=text)


def render_game_not_found_screen(code: str) -> Screen:
  return Screen(textref=TextRef("game_not_found", {"code": code}))


def render_already_in_this_game_screen() -> Screen:
  return Screen(textref=TextRef("already_in_this_game"))


def render_game_already_started_screen() -> Screen:
  return Screen(textref=TextRef("game_already_started"))


def render_input_names_screen(slots: int) -> Screen:
  return Screen(textref=TextRef("input_names", {"slots": slots}))


# --- restart_game ---

def render_game_not_started_yet_screen() -> Screen:
  return Screen(textref=TextRef("game_not_started_yet"))


def render_restart_game_broadcast_screen() -> Screen:
  return Screen(textref=TextRef("restart_game_broadcast"))


def render_restart_game_confirm_screen() -> Screen:
  buttons = [[Button(TextRef("start_game"), 'g:start_round')]]
  return Screen(textref=TextRef("restart_game_confirm"), buttons=buttons)


# --- end_game ---

def render_game_ended_by_owner_screen() -> Screen:
  return Screen(textref=TextRef("game_ended_by_owner"))


# --- leave_game / kick_player ---

def render_not_in_a_game_screen() -> Screen:
  return Screen(textref=TextRef("not_in_a_game"))


def render_kick_inavailable_screen() -> Screen:
  return Screen(textref=TextRef("kick_inavailable"))


# --- settings ---

def render_cant_edit_in_game_screen() -> Screen:
  return Screen(textref=TextRef("cant_edit_in_game"))


# --- broadcast ---

def render_broadcast_usage_screen() -> Screen:
  return Screen(textref=TextRef("broadcast_usage"))


def render_broadcast_relay_screen(formatted_message: str) -> Screen:
  return Screen(textref=TextRef("text", {"text": formatted_message}))


# --- check_game / check_ownership ---

def render_no_running_game_screen() -> Screen:
  return Screen(textref=TextRef("no_running_game"))


def render_not_owner_screen() -> Screen:
  return Screen(textref=TextRef("not_owner"))


# --- interaction routing (router.py / interaction_handlers.py) ---

def render_not_active_screen() -> Screen:
  return Screen(textref=TextRef("not_active"))


# --- lifecycle_services: player-left / ownership-transfer notifications ---

def render_player_left_game_terminated_screen(players_names: str | None) -> Screen:
  if not players_names:
    return Screen(textref=TextRef("a_player_left_game_terminated"))
  return Screen(textref=TextRef("player_left_game_terminated", {"players_names": players_names}))


def render_owner_left_game_screen() -> Screen:
  return Screen(textref=TextRef("owner_left_game"))


def render_you_became_owner_screen() -> Screen:
  return Screen(textref=TextRef("you_became_owner"))


def render_player_left_choose_mode_screen() -> Screen:
  return Screen(textref=TextRef("player_left_choose_mode"))


def render_player_left_waiting_owner_screen(players_names: str) -> Screen:
  return Screen(textref=TextRef("player_left_waiting_owner", {"players_names": players_names}))


def render_player_left_ready_to_continue_screen(players_names: str) -> Screen:
  buttons = [[Button(TextRef("continue"), "g:start_round")]]
  return Screen(textref=TextRef("player_left_ready_to_continue", {"players_names": players_names}), buttons=buttons)


# --- jobs.py: inactivity reminders ---

def render_still_alive_screen() -> Screen:
  buttons = [[Button(TextRef("yes"), "i:session_alive")]]
  return Screen(textref=TextRef("still_alive"), buttons=buttons)


def render_still_running_screen() -> Screen:
  buttons = [[Button(TextRef("yes"), "i:game_running")]]
  return Screen(textref=TextRef("still_running"), buttons=buttons)

# --- join message ---

def render_join_message_screen(username: str | None, game_id: str) -> Screen:
  if not username:
    text = TextRef("invitation_message_anonymous")
  else:
    text = TextRef("invitation_message", {"user_username": username})
  buttons = [[Button(text = TextRef("join"), url = f"https://t.me/{BOT_USERNAME}?start={game_id}")]]
  return Screen(textref = text, buttons = buttons)