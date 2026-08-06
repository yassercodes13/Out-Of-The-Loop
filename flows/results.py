from telegram import Update
from models import Game, Session
from flows.utils import set_all_substates
from flows.states import GameState
from flows.substates import ResultsSubstate
from adapters.telegram.messaging import broadcast_message, edit_message
from services.lifecycle_services import terminate_game
from texts.refs import TextRef
from views.results import render_edit_player_score_screen, render_edit_score_list_screen, render_end_game_screen, render_round_report_screen, render_round_results_screen

async def handle_results(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  refresh_all = False

  if data and data.startswith("g:round_results"):

    if session.game_substate is None:
      refresh_all = True
      set_all_substates(game, ResultsSubstate.ROUND_RESULTS, set_waited = False)

    else:
      session.game_substate = ResultsSubstate.ROUND_RESULTS
      refresh_all = len(data.split(":")) > 2

    rounds_ended = True if game.num_rounds > game.round_number else False
    result_rows = game.round_result(rewrite = refresh_all)

    screens = render_round_results_screen(rounds_ended, result_rows)
    owner_screen = screens.special
    others_screen = screens.others

    if session.id == game.owner_session_id:
      session.waited = True
      await edit_message(session, owner_screen.textref, owner_screen.buttons)
      if refresh_all:
        await broadcast_message(game, mode = "edit", text = others_screen.textref, buttons = others_screen.buttons, exclude_session_ids = [game.owner_session_id])
    else: 
      await edit_message(session, others_screen.textref, others_screen.buttons)

  elif session.game_substate == ResultsSubstate.ROUND_RESULTS:
    if data == "g:report":
      session.game_substate = ResultsSubstate.ROUND_REPORT
      screen = render_round_report_screen(round_report=game.round_report, round_number=game.round_number)
      await edit_message(session, screen.textref, screen.buttons)

    elif data == "g:end_results":
      session.game_substate = ResultsSubstate.FINAL_RESULTS
      screen = render_end_game_screen(game.final_result(), confirmed=False)
      await edit_message(session, screen.textref, screen.buttons)

    elif data and data.startswith("g:edit_score"):
      session.game_substate = ResultsSubstate.EDIT_SCORE
      screen = render_edit_score_list_screen(game.players)
      await edit_message(session, screen.textref, screen.buttons)

    elif data == "g:start_round":
      game.state = GameState.INFORM
      set_all_substates(game, None, set_waited=False)
      return True

  elif session.game_substate == ResultsSubstate.EDIT_SCORE and data and data.startswith("g:edit_score"):
    session.game_substate = ResultsSubstate.EDIT_SCORE

    parts = data.split(":")
    
    if len(parts) < 3:
      screen = render_edit_score_list_screen(game.players)
      await edit_message(session, screen.textref, screen.buttons)

    else:
      player_id = int(parts[2])
      player = game.get_player_by_id(player_id)

      if len(parts) == 4:
        edit = int(parts[3])
        old_score = player.score
        player.score += edit
        game.round_report.append(TextRef("score_updated", {"p_name": player.name, "old_score": old_score, "new_score": player.score}))

      screen = render_edit_player_score_screen(player)
      await edit_message(session, screen.textref, screen.buttons)

  elif session.game_substate == ResultsSubstate.FINAL_RESULTS:
    if data == "g:end_it":
      screen = render_end_game_screen(game.final_result(), confirmed = True)
      await broadcast_message(game, mode = "edit", text = screen.textref, buttons = screen.buttons)
      await terminate_game(game)

    elif data == "g:start_round":
      game.state = GameState.INFORM
      set_all_substates(game, None, set_waited = False)
      return True

  return False