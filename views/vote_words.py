from texts.refs import TextRef, Button, Screen, BroadcastScreens

def render_vote_words_start_screen() -> Screen:
  text = TextRef("vote_words_intro")
  buttons = [[Button(TextRef("start_voting"), "g:start_voting")]]
  return Screen(textref=text, buttons=buttons)


def render_voting_screen(voter_name: str, other_team: str, choices: list[str], prefix: str) -> Screen:
  text = TextRef("vote_prompt", {"voter_name": voter_name, "other_team": other_team})
  buttons = [
    [Button(TextRef("text", {"text": choice}), f"g:{prefix}_choice:{i}")]
    for i, choice in enumerate(choices)
  ]
  return Screen(textref=text, buttons=buttons)


def render_waiting_screen() -> Screen:
  text = TextRef("waiting_voting")
  return Screen(textref=text, buttons=None)


def render_vote_result_screen(result_message) -> BroadcastScreens:
  text = TextRef("see_results_prompt", {"result_message": result_message})
  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("see_results"), "g:round_results")]]
  )
  others_screen = Screen(textref=text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)