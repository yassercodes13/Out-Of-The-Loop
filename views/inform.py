from models.role import Role
from texts.refs import TextRef, Button, Screen, BroadcastScreens
from models.player import Player

def render_round_info_screen(round_number: int, category: str, mode_label: str) -> Screen:
  """Screen shown to all players at the start of a round."""

  text = TextRef("round_info", {
    "round_number": round_number,
    "category": category,
    "mode": mode_label
  })
  buttons = [[Button(TextRef("got_it"), "g:start_informing")]]
  return Screen(textref=text, buttons=buttons)


def render_show_info_screen(player: Player) -> Screen:
  """Screen shown to a player when they tap 'That's me!' to see their info."""

  if player.role == Role.DETECTIVE:
    text = TextRef("show_info_detective", {
      "p_name": player.name,
      "p_role": TextRef(f"role_{player.role.value}"),
      "p_alpha_word": player.alpha_word,
      "p_beta_word": player.beta_word,
      "p_current_score": player.score
    })
  else:
    prefix = TextRef("your_team") if player.role in ["alpha", "beta"] else TextRef("your_role")
    text = TextRef("show_info_player", {
      "p_name": player.name,
      "p_word": player.word,
      "p_prefix": prefix,
      "p_role": TextRef(f"role_{player.role.value}"),
      "p_current_score": player.score
    })
  buttons = [[Button(TextRef("got_it"), "g:next")]]
  return Screen(textref=text, buttons=buttons)


def render_hide_info_screen(player: Player, turn_index: int, has_seen: bool) -> Screen:
  """
  Screen shown before revealing info: 'Give phone to X'.
  has_seen indicates if this player already viewed their info (so we can show 'Skip').
  """
  text = TextRef("give_phone_to", {"p_name": player.name})
  buttons = [[Button(TextRef("thats_me"), "g:show")]]

  if turn_index > 0:
    buttons.append([Button(TextRef("back"), "g:back")])

  if has_seen:
    buttons.append([Button(TextRef("skip"), "g:next")])

  return Screen(textref=text, buttons=buttons)


def render_end_inform_screen(all_ready: bool, extra_informs: list[TextRef]) -> Screen | BroadcastScreens:
  """
  End of informing: either waiting for others, or owner gets a button to proceed.
  Returns a Screen for non-owner, or BroadcastScreens for owner (separate screens for owner vs others).
  """
  text = [TextRef("all_informed")]
  text.append(TextRef("text", {"text": "\n\n"}))
  text.extend(extra_informs)

  if all_ready:
    # Owner gets a button to start questioning
    owner_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("all_ready")]
    owner_buttons = [[Button(TextRef("start_questioning"), "g:start_question")]]
    owner_screen = Screen(textref=owner_text, buttons=owner_buttons)

    # Others get only the text (no button)
    others_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("all_ready")]
    others_screen = Screen(textref=others_text, buttons=None)

    return BroadcastScreens(special=owner_screen, others=others_screen)
  else:
    # Not all ready: everyone sees the same waiting text
    waiting_text = text + [TextRef("text", {"text": "\n\n"}), TextRef("waiting_others_finish")]
    return Screen(textref=waiting_text, buttons=None)