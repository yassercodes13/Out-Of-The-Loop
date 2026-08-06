from texts.refs import TextRef, Button, Screen
from models.modes import GameMode

def render_end_questions_screen(mode: GameMode) -> Screen:
  """Screen shown to the owner after all questions are done."""
  if mode == GameMode.TEAMS:
    text = TextRef("ready_vote_teams")
  else:
    text = TextRef("ready_vote_outsider")
  buttons = [
    [Button(TextRef("start_voting"), "g:start_vote")],
    [Button(TextRef("extra_questions"), "g:extra_questions")],
  ]
  return Screen(textref=text, buttons=buttons)


def render_ask_question_screen(asker_name: str, answerer_name: str, show_back: bool) -> Screen:
  """
  Screen shown to the asker (with buttons) and broadcasted to others (text only).
  show_back controls whether the 'Back' button appears.
  """
  text = TextRef("ask_question", {"asker": asker_name, "answerer": answerer_name})
  buttons = [[Button(TextRef("next"), "g:next")]]
  if show_back:
    buttons.append([Button(TextRef("back"), "g:back")])
  return Screen(textref=text, buttons=buttons)

def render_waiting_for_owner_screen() -> Screen:
  """Screen shown to non‑owners when questioning is done and they wait for owner."""
  text = TextRef("waiting_for_owner_to_start_voting")
  return Screen(textref=text, buttons=None)