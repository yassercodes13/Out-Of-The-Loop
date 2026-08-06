from texts.refs import TextRef, Button, Screen
from models.modes import GameMode
from models.user import User

def render_mode_settings_screen(user: User, show_back_to_game: bool) -> Screen:
  """
  Renders the mode settings screen.
  show_back_to_game: if True, shows a 'Back to mode selection' button (when in a game).
  if False, shows 'Back to Settings' (when in standalone settings).
  """
  text = TextRef("mode_settings_info", {"min_players": user.min_players_for_random})
  buttons = []
  for mode in GameMode:
    if mode == GameMode.RANDOM:
      continue
    label = mode.label + (" ✔" if mode in user.random_modes else " ✘")
    buttons.append([Button(TextRef("text", {"text": label}), f'e:toggle:{mode.name}')])

  if show_back_to_game:
    buttons.append([Button(TextRef("back_to_mode_selection"), 's:choose_mode')])
  else:
    buttons.append([Button(TextRef("back_to_settings"), 'e:done')])

  return Screen(textref=text, buttons=buttons)


def render_min_two_modes_popup() -> Screen:
  return Screen(textref=TextRef("min_two_modes"), buttons=[[Button(TextRef("ok"), "e:done")]])