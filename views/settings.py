from texts.refs import TextRef, Button, Screen

def render_settings_menu_screen() -> Screen:
  """Main settings menu (categories, modes, language, done)."""
  text = TextRef("choose_edit")
  buttons = [
    [Button(TextRef("categories"), "e:categories")],
    [Button(TextRef("modes"), "e:modes")],
    [Button(TextRef("language"), "e:language")],
    [Button(TextRef("done"), "e:done")],
  ]
  return Screen(textref=text, buttons=buttons)


def render_settings_saved_screen() -> Screen:
  """Settings saved confirmation (no buttons)."""
  text = TextRef("settings_saved")
  return Screen(textref=text, buttons=None)