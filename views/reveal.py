from texts.refs import TextRef, Button, Screen, BroadcastScreens
from models.game import Game
from models.player import Player

def render_single_outsider_screen(outsider_name: str) -> BroadcastScreens:
  """Reveals the only outsider: owner gets button to guess word, others get text only."""
  text = TextRef("single_outsider_reveal", {"name": outsider_name})
  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("guess_word"), "g:guess_word:0")]]
  )
  others_screen = Screen(textref=text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)


def render_double_outsider_screen(outsider_name: str) -> BroadcastScreens:
  """Double outsider: owner (the most voted outsider) gets two choices: guess word or guess other outsider."""
  reveal_text = [TextRef("most_voted_outsider_reveal", {"name": outsider_name})]
  choices_text = reveal_text + [TextRef("double_outsider_choices", {"name": outsider_name})]
  owner_screen = Screen(
    textref=choices_text,
    buttons=[
      [Button(TextRef("guess_word"), "g:guess_word:0")],
      [Button(TextRef("guess_outsider"), "g:guess_outsider")]
    ]
  )
  # Others get only the reveal text (no choices)
  others_screen = Screen(textref=reveal_text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)


def render_detective_reveal_screen(detective_name: str) -> BroadcastScreens:
  """Reveal detective: owner (the detective) gets button to guess team members."""
  text = TextRef("detective_reveal", {"name": detective_name})
  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("guess_team_members"), "g:guess_teams")]]
  )
  others_screen = Screen(textref=text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)


def render_teams_reveal_screen(alphas_names: list[str], betas_names: list[str]) -> BroadcastScreens:
  """Reveal teams: owner gets button to vote words, others get text only."""
  text = TextRef("teams_reveal", {"alphas": ", ".join(alphas_names), "betas": ", ".join(betas_names)})
  owner_screen = Screen(
    textref=text,
    buttons=[[Button(TextRef("vote_words"), "g:vote_words")]]
  )
  others_screen = Screen(textref=text, buttons=None)
  return BroadcastScreens(special=owner_screen, others=others_screen)