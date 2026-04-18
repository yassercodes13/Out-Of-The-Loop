from flows.msg_utils import *
from handlers.utils import end_game
from flows.states import GameState
from flows.substates import ResultsSubstate
from telegram import InlineKeyboardButton, Update

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
    text = ""
    if len(data.split(":")) > 2:
      text = game.round_result(rewrite = True)
      refresh_all = True
    else:
      text = game.round_result(rewrite = False)
    
    buttons = [[InlineKeyboardButton("Round Report", callback_data="g:report")]]
    if session.user_id == game.owner_id:
      buttons.append([InlineKeyboardButton("Edit Score", callback_data = "g:edit_score")])
      if game.num_rounds > game.round_number:
        buttons.append([InlineKeyboardButton("Next Round", callback_data = "g:start_round")])
      else:
        buttons.append([InlineKeyboardButton("Extra Round", callback_data = "g:start_round")])
      buttons.append([InlineKeyboardButton("End Game", callback_data = "g:end_results")])
    
    await edit_message(session, text, buttons)
    
    if refresh_all:
      guest_buttons = [[InlineKeyboardButton(text = "Round Report", callback_data = "g:report")]]
      await broadcast_message(game = game, mode = "edit", text = text, buttons = guest_buttons, exclude_chat_ids = [session.chat_id])

  elif session.game_substate == ResultsSubstate.ROUND_REPORT and data == "g:report":
    text = game.round_report
    buttons = [[InlineKeyboardButton("Back", callback_data = 'g:round_results')]]
    
    await edit_message(session, text, buttons)

  elif session.game_substate == ResultsSubstate.FINAL_RESULTS and data in ["g:end_it", "g:end_results"]:
    buttons = []
    text = game.final_result()
    if data == "g:end_it":
      end_game(game)
    else:
      buttons = [
        [InlineKeyboardButton("End it", callback_data = "g:end_it")],
        [InlineKeyboardButton("Get back", callback_data = "g:round_results")]
      ]
      text += "\nSure you want to end?"
    

    await edit_message(session, text, buttons)


  elif session.game_substate == ResultsSubstate.EDIT_SCORE and data and data.startswith("g:edit_score"):
    parts = data.split(":")
    if len(parts) < 3:  
      text = "Tap the player you want to edit their score"
      buttons = [[InlineKeyboardButton(player.name, callback_data = f"g:edit_score:{player.id}")] for player in game.players]
      buttons.append([InlineKeyboardButton("Done", callback_data = "g:round_results:rewrite")])
    else:
      player_id = int(parts[2])
      edit = 0
      player = game.get_player_by_id(player_id)
      
      if len(parts) == 4:
        edit = int(parts[3])
        player.score += edit
        game.round_report += f"\nScore of {player.name} updated by owner from {player.score - edit} to {player.score}."

      text = f"Current Score of {player.name}: {player.score}"
      buttons = [
        [InlineKeyboardButton("+2", callback_data = f"g:edit_score:{player.id}:+2"), InlineKeyboardButton("-2", callback_data = f"g:edit_score:{player.id}:-2")],
        [InlineKeyboardButton("+5", callback_data = f"g:edit_score:{player.id}:+5"), InlineKeyboardButton("-5", callback_data = f"g:edit_score:{player.id}:-5")],
        [InlineKeyboardButton("Another Player", callback_data = "g:edit_score")],
        [InlineKeyboardButton("Done", callback_data = "g:round_results:rewrite")],
      ]
    
    await edit_message(session, text, buttons)

  return False