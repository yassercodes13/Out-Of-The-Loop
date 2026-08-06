from texts.refs import TextRef, Button, Screen
from texts import supported_langs

def render_language_settings_screen(current_lang: str) -> Screen:
  """Renders language selection screen with checkmarks."""
  buttons = []
  for lang in supported_langs:
    chosen = "_chosen" if current_lang == lang else ""
    button = Button(TextRef(f"language_{lang}{chosen}"), f"e:language:{lang}")
    buttons.append([button])
  buttons.append([Button(TextRef("done"), "e:done")])
  return Screen(textref=TextRef("language_main"), buttons=buttons)