from flows.msg_utils import *
from handlers.utils import end_game
from flows.states import GameState
from flows.substates import ResultsSubstate
from telegram import InlineKeyboardButton, Update

async def handle_results(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  refresh_all = False

  if data == "g:results":
    if session.game_substate is None:
      refresh_all = True
      set_all_substates(game, ResultsSubstate.ROUND_RESULTS)
  
    session.game_substate = ResultsSubstate.ROUND_RESULTS
  
  elif data == "g:report" and session.game_substate == ResultsSubstate.ROUND_RESULTS:
    session.game_substate = ResultsSubstate.ROUND_REPORT
  
  elif data == "g:end_results" and session.game_substate == ResultsSubstate.ROUND_RESULTS:
    session.game_substate = ResultsSubstate.FINAL_RESULTS
  
  elif data == "g:start_round" and session.game_substate in [ResultsSubstate.FINAL_RESULTS, ResultsSubstate.ROUND_RESULTS]:
    game.state = GameState.INFORM
    set_all_substates(game, None)
    return True
    

  if session.game_substate == ResultsSubstate.ROUND_RESULTS:
    text = game.round_result()
    buttons = [[InlineKeyboardButton("Show Round Report", callback_data="g:report")]]
    if session.user_id == game.owner_id:
      buttons.append([InlineKeyboardButton("End Game", callback_data="g:end_results")])
      if game.num_rounds > game.round_number:
        buttons.append([InlineKeyboardButton("Next Round", callback_data = "g:start_round")])
    
    await edit_message(session, text, buttons)
    
    if refresh_all:
      guest_buttons = [[InlineKeyboardButton(text = "Round Report", callback_data = "g:report")]]
      await broadcast_message(game = game, mode = "edit", text = text, buttons = guest_buttons, exclude_chat_ids = [session.chat_id])

  elif session.game_substate == ResultsSubstate.ROUND_REPORT and data == "g:report":
    text = game.round_report
    buttons = [[InlineKeyboardButton("Back", callback_data = 'g:results')]]
    
    await edit_message(session, text, buttons)

  elif session.game_substate == ResultsSubstate.FINAL_RESULTS and data in ["g:enough", "g:end_results"]:
    buttons = []
    if data == "g:enough":
      end_game(game)
    else:
      buttons = [
        [InlineKeyboardButton("Play an Extra Round", callback_data = "g:start_round")],
        [InlineKeyboardButton("Nope. Enough.", callback_data = "g:enough")]
      ]
    
    text = game.final_result()

    await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [session.chat_id])
    await edit_message(session, text, buttons)

  return False
