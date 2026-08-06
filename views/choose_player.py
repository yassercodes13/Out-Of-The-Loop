from texts.refs import TextRef, Button, Screen
from models.player import Player

def render_players_screen(players: list[Player], all_option: bool = False) -> Screen:
  """Screen to select a player (or all) to remove."""
  text = TextRef("choose_the_player")
  buttons = [
    [Button(TextRef("text", {"text": f"{p.name}"}), f"i:player:{p.id}")]
    for p in players
  ]
  if all_option:
    buttons.append([Button(TextRef("all"), "i:remove_all")])
  buttons.append([Button(TextRef("cancel"), "i:cancel")])
  return Screen(textref=text, buttons=buttons)