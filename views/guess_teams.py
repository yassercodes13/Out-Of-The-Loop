from texts.refs import TextRef, Button, Screen, BroadcastScreens

def render_detective_waiting_screen() -> Screen:
  """Screen shown to other players while the detective is guessing."""
  text = TextRef("detective_will_guess")
  return Screen(textref=text, buttons=None)

def render_guessing_screen(players_info: list[tuple]) -> Screen:
  """
  Screen for the detective to assign teams.
  players_info: list of (player_id, player_name, current_team_label)
  where team_label is 'alpha' or 'beta'.
  """
  text = TextRef("assign_teams")
  buttons = []
  for pid, pname, team in players_info:
    # team is "alpha" or "beta" -> used in TextRef key
    buttons.append([
      Button(TextRef(f"player_team_{team}", {"p_name": pname}), f"g:toggle_{pid}")
    ])
  buttons.append([Button(TextRef("confirm"), "g:confirm_guess")])
  return Screen(textref=text, buttons=buttons)


def render_result_screen(result_text: str, alphas_names: list[str], betas_names: list[str]) -> BroadcastScreens:
  """After detective guesses: owner gets a button, others get text only."""
  text = TextRef(
    "guess_result",
    {
      "result_text": result_text,
      "alphas": ", ".join(alphas_names),
      "betas": ", ".join(betas_names)
    }
  )
  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("vote_words"), "g:vote_words")]]
  )
  others_screen = Screen(textref=text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)