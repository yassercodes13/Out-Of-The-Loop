from config import SCORE_EDIT_STEPS
from flows.utils import *
from handlers.utils import end_game
from flows.states import GameState
from flows.substates import ResultsSubstate
from telegram import Update
from models.player import Player
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button


# --- text builders ---

def render_report_text(game: Game) -> str:
  text = [TextRef("round_report_header", {"round_number": game.round_number})]
  text.extend(game.round_report)
  return text


def render_result_text(game: Game, rewrite: bool = False) -> str:
  rows = game.round_result(rewrite=rewrite)
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
  return text


def render_final_result_text(game: Game) -> list[tuple[str, dict]]:
  data = game.final_result()
  if data["tie"]:
    return [TextRef("final_result_tie", {"score": data["winning_score"]})]

  text  = [TextRef("final_result_winners_plural") if len(data["winners"]) > 1 else TextRef("final_result_winner_single")]

  winners_rows = "\n".join(f"👑 {name}" for name in data["winners"])
  winners_rows += "\n\n"
  text.append(TextRef("text", {"text" : winners_rows}))

  text.append(TextRef("final_result_losers_plural") if len(data["losers"]) > 1 else TextRef("final_result_loser_single"))

  losers_rows = "\n".join(f"😭 {name}" for name in data["losers"])
  text.append(TextRef("text", {"text" : losers_rows}))
  return text


# --- screen renderers ---

async def render_round_results_screen(session: Session, game: Game, text: str, broadcast: bool = False):
  buttons = [[Button(TextRef("round_report"), "g:report")]]
  if session.user_id == game.owner_id:
    buttons.append([Button(TextRef("edit_score"), "g:edit_score")])
    session.waited = True
    if game.num_rounds > game.round_number:
      buttons.append([Button(TextRef("next_round"), "g:start_round")])
    else:
      buttons.append([Button(TextRef("extra_round"), "g:start_round")])
    buttons.append([Button(TextRef("end_game"), "g:end_results")])

  await edit_message(session, text, buttons)

  if broadcast:
    guest_buttons = [[Button(TextRef("round_report"), "g:report")]]
    await broadcast_message(game=game, mode="edit", text=text, buttons=guest_buttons, exclude_chat_ids=[session.chat_id])


async def render_round_report_screen(session: Session, game: Game):
  buttons = [[Button(TextRef("back"), "g:round_results")]]
  await edit_message(session, render_report_text(game), buttons)


async def render_end_game_confirm_screen(session: Session, game: Game):
  text = render_final_result_text(game) 
  text.append(TextRef("sure_end"))
  buttons = [
    [Button(TextRef("end_it"),   "g:end_it")],
    [Button(TextRef("get_back"), "g:round_results")]
  ]
  await edit_message(session, text, buttons)


async def render_edit_score_list_screen(session: Session, game: Game):
  text = TextRef("edit_score_prompt")
  buttons = [[Button(TextRef("text", {"text" : player.name}), f"g:edit_score:{player.id}")] for player in game.players]
  buttons.append([Button(TextRef("done"), "g:round_results:rewrite")])
  await edit_message(session, text, buttons)


async def render_edit_player_score_screen(session: Session, player: Player):
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
  await edit_message(session, text, buttons)


# --- dispatch ---

async def handle_results(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  refresh_all = False

  if data and data.startswith("g:round_results"):
    if session.game_substate is None:               # State entry point
      refresh_all = True
      set_all_substates(game, ResultsSubstate.ROUND_RESULTS, set_waited = False)
    else: #Just getting back to Main Screen
      session.game_substate = ResultsSubstate.ROUND_RESULTS

  elif data == "g:start_round" and session.game_substate in [ResultsSubstate.FINAL_RESULTS, ResultsSubstate.ROUND_RESULTS]:
    game.state = GameState.INFORM
    set_all_substates(game, None, set_waited = False)
    return True

  elif session.game_substate == ResultsSubstate.ROUND_RESULTS:
    if data == "g:report":
      session.game_substate = ResultsSubstate.ROUND_REPORT

    elif data == "g:end_results":
      session.game_substate = ResultsSubstate.FINAL_RESULTS

    elif data == "g:edit_score":
      session.game_substate = ResultsSubstate.EDIT_SCORE


  if session.game_substate == ResultsSubstate.ROUND_RESULTS and data and data.startswith("g:round_results"):
    rewrite = len(data.split(":")) > 2
    text = render_result_text(game, rewrite = rewrite)
    if rewrite:
      refresh_all = True
    await render_round_results_screen(session, game, text, broadcast = refresh_all)

  elif session.game_substate == ResultsSubstate.ROUND_REPORT and data == "g:report":
    await render_round_report_screen(session, game)

  elif session.game_substate == ResultsSubstate.FINAL_RESULTS and data == "g:end_it":
    text = render_final_result_text(game)
    await end_game(game)
    await edit_message(session, text)

  elif session.game_substate == ResultsSubstate.FINAL_RESULTS and data == "g:end_results":
    await render_end_game_confirm_screen(session, game)

  elif session.game_substate == ResultsSubstate.EDIT_SCORE and data and data.startswith("g:edit_score"):
    parts = data.split(":")
    if len(parts) < 3:
      await render_edit_score_list_screen(session, game)
    else:
      player_id = int(parts[2])
      player = game.get_player_by_id(player_id)

      if len(parts) == 4:
        edit = int(parts[3])
        old_score = player.score
        player.score += edit
        game.round_report.append(TextRef("score_updated", {"p_name": player.name, "old_score": old_score, "new_score": player.score}))

      await render_edit_player_score_screen(session, player)

  return False