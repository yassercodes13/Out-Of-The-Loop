from config import SCORE_EDIT_STEPS
from flows.utils import *
from handlers.utils import end_game
from flows.states import GameState
from flows.substates import ResultsSubstate
from telegram import InlineKeyboardButton, Update
from texts import t, b
from adapters.telegram.messaging import *


# --- text builders (model returns structured data, we render it here) ---

def render_report_text(game: Game) -> str:
  text = t("round_report_header", round_number=game.round_number)
  for key, kwargs in game.round_report:
    rendered = {
      k: t(f"role_{v}") if k == "target_role" else
         t(f"team_{v}") if k == "team" else v
      for k, v in kwargs.items()
    }
    text += t(key, **rendered)
  return text


def render_result_text(game: Game, rewrite: bool = False) -> str:
  rows = game.round_result(rewrite=rewrite)
  text = t("round_results_header")
  for row in rows:
    text += t("round_result_row",
      arrow = row["arrow"],
      name  = row["name"],
      role  = t(f"role_{row['role']}"),
      score = row["score"],
    )
  return text


def render_final_result_text(game: Game) -> str:
  data = game.final_result()
  if data["tie"]:
    return t("final_result_tie", score=data["winning_score"])
  text  = t("final_result_winners_plural") if len(data["winners"]) > 1 else t("final_result_winner_single")
  text += "\n".join(f"👑 {name}" for name in data["winners"])
  text += "\n\n"
  text += t("final_result_losers_plural") if len(data["losers"]) > 1 else t("final_result_loser_single")
  text += "\n".join(f"😭 {name}" for name in data["losers"])
  return text


# --- screen renderers ---

async def render_round_results_screen(session: Session, game: Game, text: str, broadcast: bool = False):
  buttons = [[InlineKeyboardButton(b("round_report"), callback_data="g:report")]]
  if session.user_id == game.owner_id:
    buttons.append([InlineKeyboardButton(b("edit_score"), callback_data="g:edit_score")])
    if game.num_rounds > game.round_number:
      buttons.append([InlineKeyboardButton(b("next_round"), callback_data="g:start_round")])
    else:
      buttons.append([InlineKeyboardButton(b("extra_round"), callback_data="g:start_round")])
    buttons.append([InlineKeyboardButton(b("end_game"), callback_data="g:end_results")])

  await edit_message(session, text, buttons)

  if broadcast:
    guest_buttons = [[InlineKeyboardButton(b("round_report"), callback_data="g:report")]]
    await broadcast_message(game=game, mode="edit", text=text, buttons=guest_buttons, exclude_chat_ids=[session.chat_id])


async def render_round_report_screen(session: Session, game: Game):
  buttons = [[InlineKeyboardButton(b("back"), callback_data="g:round_results")]]
  await edit_message(session, render_report_text(game), buttons)


async def render_end_game_confirm_screen(session: Session, game: Game):
  text = render_final_result_text(game) + t("sure_end")
  buttons = [
    [InlineKeyboardButton(b("end_it"),   callback_data="g:end_it")],
    [InlineKeyboardButton(b("get_back"), callback_data="g:round_results")]
  ]
  await edit_message(session, text, buttons)


async def render_edit_score_list_screen(session: Session, game: Game):
  text = t("edit_score_prompt")
  buttons = [[InlineKeyboardButton(player.name, callback_data=f"g:edit_score:{player.id}")] for player in game.players]
  buttons.append([InlineKeyboardButton(b("done"), callback_data="g:round_results:rewrite")])
  await edit_message(session, text, buttons)


async def render_edit_player_score_screen(session: Session, player):
  text = t("player_current_score", p_name=player.name, score=player.score)
  buttons = []
  for step in SCORE_EDIT_STEPS:
    buttons.append(
      [
        InlineKeyboardButton(
          f"+{step}",
          callback_data=f"g:edit_score:{player.id}:+{step}"
        ),
        InlineKeyboardButton(
          f"-{step}",
          callback_data=f"g:edit_score:{player.id}:-{step}"
        )
      ]
    )
  await edit_message(session, text, buttons)


# --- dispatch ---

async def handle_results(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  refresh_all = False

  if data and data.startswith("g:round_results"):
    if session.game_substate is None:
      refresh_all = True
      set_all_substates(game, ResultsSubstate.ROUND_RESULTS)
    session.game_substate = ResultsSubstate.ROUND_RESULTS

  elif data == "g:report" and session.game_substate == ResultsSubstate.ROUND_RESULTS:
    session.game_substate = ResultsSubstate.ROUND_REPORT

  elif data == "g:end_results" and session.game_substate == ResultsSubstate.ROUND_RESULTS:
    session.game_substate = ResultsSubstate.FINAL_RESULTS

  elif data == "g:edit_score" and session.game_substate == ResultsSubstate.ROUND_RESULTS:
    session.game_substate = ResultsSubstate.EDIT_SCORE

  elif data == "g:start_round" and session.game_substate in [ResultsSubstate.FINAL_RESULTS, ResultsSubstate.ROUND_RESULTS]:
    game.state = GameState.INFORM
    set_all_substates(game, None)
    return True


  if session.game_substate == ResultsSubstate.ROUND_RESULTS and data and data.startswith("g:round_results"):
    rewrite = len(data.split(":")) > 2
    text = render_result_text(game, rewrite=rewrite)
    if rewrite:
      refresh_all = True
    await render_round_results_screen(session, game, text, broadcast=refresh_all)

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
        game.round_report.append(("score_updated", {"p_name": player.name, "old_score": old_score, "new_score": player.score}))

      await render_edit_player_score_screen(session, player)

  return False