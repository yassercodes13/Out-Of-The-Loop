from models.player import Player
from texts.refs import TextRef, Button, Screen, BroadcastScreens
from config import SCORE_EDIT_STEPS

def render_round_results_screen(rounds_ended: bool, rows: list[dict]):
  text = [TextRef("round_results_header")]

  for row in rows:
    text.append(
      TextRef("round_result_row", {
        "arrow" : row["arrow"],
        "name"  : row["name"],
        "role"  : row["role"],
        "score" : row["score"],
      })
    )

  special_buttons = [
    [Button(TextRef("round_report"), "g:report")],
    [Button(TextRef("edit_score"), "g:edit_score")]
  ]

  if rounds_ended:
    special_buttons.append([Button(TextRef("next_round"), "g:start_round")])
  else:
    special_buttons.append([Button(TextRef("extra_round"), "g:start_round")])
  special_buttons.append([Button(TextRef("end_game"), "g:end_results")])

  buttons = [
    [Button(TextRef("round_report"), "g:report")]
  ]

  return BroadcastScreens(
    special = Screen(textref = text, buttons = special_buttons),
    others = Screen(textref = text, buttons = buttons)
  )

def render_round_report_screen(round_report, round_number):
  text = [TextRef("round_report_header", {"round_number": round_number})]
  text.extend(round_report)  
  buttons = [[Button(TextRef("back"), "g:round_results")]]
  return Screen(textref = text, buttons = buttons)

def render_edit_score_list_screen(players: list[Player]):
  text = TextRef("edit_score_prompt")
  buttons = [[Button(TextRef("text", {"text" : player.name}), f"g:edit_score:{player.id}")] for player in players]
  buttons.append([Button(TextRef("done"), "g:round_results:rewrite")])

  return Screen(textref = text, buttons = buttons)

def render_edit_player_score_screen(player: Player):
  text = TextRef("player_current_score", {"p_name": player.name, "score": player.score})
  buttons = []
  for step in SCORE_EDIT_STEPS:
    buttons.append(
      [Button(TextRef("text", {"text" : f"+{step}"}),
          f"g:edit_score:{player.id}:+{step}"
        ),
        Button(TextRef("text", {"text" : f"-{step}"}),
          f"g:edit_score:{player.id}:-{step}"
      )]
    )
  buttons.append([Button(TextRef("done"), "g:edit_score")])

  return Screen(textref = text, buttons = buttons)


def render_end_game_screen(data: dict, confirmed: bool):
  if data["tie"]:
    text = [TextRef("final_result_tie", {"score": data["winning_score"]})]
  else:
    text  = [TextRef("final_result_winners_plural") if len(data["winners"]) > 1 else TextRef("final_result_winner_single")]
    winners_rows = "\n".join(f"👑 {name}" for name in data["winners"]) + "\n\n"
    text.append(TextRef("text", {"text" : winners_rows}))

    text.append(TextRef("final_result_losers_plural") if len(data["losers"]) > 1 else TextRef("final_result_loser_single"))
    losers_rows = "\n".join(f"😭 {name}" for name in data["losers"])
    text.append(TextRef("text", {"text" : losers_rows}))

  buttons = None

  if not confirmed:
    text.append(TextRef("sure_end"))
    buttons = [
      [Button(TextRef("end_it"),   "g:end_it")],
      [Button(TextRef("get_back"), "g:round_results")]
    ]
  return Screen(textref = text, buttons = buttons)
