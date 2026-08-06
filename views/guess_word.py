from texts.refs import TextRef, Button, Screen, BroadcastScreens

def render_waiting_screen(guesser_name: str) -> Screen:
  """Screen shown to other players while the guesser is choosing."""
  text = TextRef("is_guessing", {"name": guesser_name})
  return Screen(textref = text)

def render_choose_word_screen(guesser_name: str, choices: list[str]) -> Screen:
  """Screen shown to the guesser to pick a word."""
  text = TextRef("try_guess", {"name": guesser_name})
  buttons = [
    [Button(TextRef("text", {"text": choice}), f"g:choice:{i}")]
    for i, choice in enumerate(choices)
  ]
  return Screen(textref=text, buttons=buttons)

def render_guess_result_screen(word: str, correct: bool, correct_word: str) -> BroadcastScreens:
  """Screens shown after guessing: owner gets buttons, others get just text."""
  if correct:
    result_message = TextRef("word_correct", {"word": word})
  else:
    result_message = TextRef("word_wrong", {"word": word, "correct_word": correct_word})

  text = TextRef("let's_see_results", {"result_message": result_message})

  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("see_results"), "g:round_results")]]
  )
  others_screen = Screen(textref=text, buttons=None)

  return BroadcastScreens(special=owner_screen, others=others_screen)