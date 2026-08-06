from texts.refs import TextRef, Button, Screen, BroadcastScreens
from models.game import GameMode

def render_start_vote_broadcast(text: TextRef | list[TextRef]) -> Screen:
  """Screen broadcasted to others when voting starts (they get a 'Start Voting' button)."""
  buttons = [[Button(TextRef("start_voting"), "g:revote")]]
  return Screen(textref=text, buttons=buttons)


def render_select_vote_screen(voter_name: str, other_players: list[tuple[str, int]], mode: GameMode) -> Screen:
  """
  Screen shown to a player to select who to vote for.
  other_players: list of (name, player_id) for players other than the voter.
  """
  text_key = "vote_other_team" if mode == GameMode.TEAMS else "vote_outsider"
  text = TextRef(text_key, {"voter_name": voter_name})
  buttons = [[Button(TextRef("text", {"text": name}), f"g:vote_{pid}")] for name, pid in other_players]
  return Screen(textref=text, buttons=buttons)


def render_confirm_vote_screen(voter_name: str, voted_name: str) -> Screen:
  """Confirm vote screen."""
  text = TextRef("confirm_vote_prompt", {"voter_name": voter_name, "voted_name": voted_name})
  buttons = [
    [Button(TextRef("yes_confirm"), "g:confirm")],
    [Button(TextRef("no_choose_again"), "g:revote")]
  ]
  return Screen(textref=text, buttons=buttons)


def render_end_vote_screen(all_ready: bool, reveal_button_key: str) -> Screen | BroadcastScreens:
  """
  End of voting.
  - If all_ready and is_owner: return BroadcastScreens (owner gets button, others get text only).
  - Else: return a single Screen with waiting text (no buttons for anyone).
  """
  text = [TextRef("done_voting")]

  if all_ready:
    # Owner gets a button to reveal
    owner_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("all_ready")]
    owner_buttons = [[Button(TextRef(reveal_button_key), "g:reveal")]]
    owner_screen = Screen(textref=owner_text, buttons=owner_buttons)

    # Others get only the text (no button)
    others_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("waiting_others_vote")]
    others_screen = Screen(textref=others_text, buttons=None)

    return BroadcastScreens(special=owner_screen, others=others_screen)
  else:
    # Not all ready: everyone sees waiting text
    waiting_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("waiting_others_vote")]
    return Screen(textref=waiting_text, buttons=None)