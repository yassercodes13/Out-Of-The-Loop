from texts.refs import TextRef, Button, Screen

def render_paused_screen(current_players: int) -> Screen:
  """Screen shown when game is paused due to insufficient players."""
  text = TextRef("game_paused_not_enough_players", {"current_players": current_players})
  buttons = [[Button(TextRef("end_game"), "g:end_paused")]]
  return Screen(textref=text, buttons=buttons)