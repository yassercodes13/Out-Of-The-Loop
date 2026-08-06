from texts.refs import TextRef, Button, Screen
from models import Game

def render_guess_outsider_screen(game: Game):
  text = TextRef("choose_outsider")
  buttons = []
  for p in game.players:
    if p != game.outsiders[0]:
      buttons.append([Button(TextRef("text", {"text": p.name}), f"g:guess:{p.id}")])
  return Screen(textref = text, buttons = buttons)

def render_result_screen(is_correct: bool, outsider_name: str):
  text = TextRef("outsider_correct") if is_correct else TextRef("outsider_wrong", {"name": outsider_name})
  buttons = [[Button(TextRef("guess_word"), "g:guess_word:1")]]
  return Screen(textref = text, buttons = buttons)