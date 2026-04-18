from flows.msg_utils import *
from flows.states import GameState
from flows.substates import VoteWordsSubstate
from telegram import InlineKeyboardButton, Update

async def handle_vote_words(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None


  if data == "g:vote_words" and session.game_substate is None:
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteWordsSubstate.START)
    start_text = "You should try to vote the other team's word.\nThe Entire team gets points for one word after voting.\n\nThe only word that counts is the one that has most votes.\nIf there is a tie the game chooses randomly between the tied words.\n\nYou can and should discuss with your team before voting."
    await broadcast_message(game = game, mode = "edit", text = start_text, buttons = [[InlineKeyboardButton("Start Voting", callback_data = "g:start_voting")]])
  
  
  if (data == "g:start_voting" and session.game_substate == VoteWordsSubstate.START) or (session.game_substate == VoteWordsSubstate.VOTING and "_choice" in query.data):
    
    if session.turn_index >= len(session.players):
      session.game_substate = VoteWordsSubstate.RESULT
      vote = False
    else:
      voter = session.players[session.turn_index]
      vote = True


    if vote and voter == game.detective:
      session.turn_index += 1
      if (session.turn_index) >= len(session.players):
        vote = False
        session.game_substate = VoteWordsSubstate.RESULT
      else:
        voter = session.players[session.turn_index]
    
    if vote:
      session.game_substate = VoteWordsSubstate.VOTING

      if voter in game.alphas:
        choices = game.alpha_choices
        other_team = "Beta"
        prefix = "a"

      elif voter in game.betas:
        choices = game.beta_choices
        other_team = "Alpha"
        prefix = "b"

      buttons = []
      for i,choice in enumerate(choices):
        buttons.append([InlineKeyboardButton(choice, callback_data=f"g:{prefix}_choice:{i}")])
      
      text = f"{voter.name}, Vote for what you think is the word of team {other_team}\n"

      await edit_message(session, text, buttons)
      session.turn_index += 1


  if data.startswith("g:a_choice:"):
    word_idx = int(data.replace("g:a_choice:", ""))
    word = game.alpha_choices[word_idx]
    word_votes = game.alphas_guesses.get(word, 0)
    word_votes += 1
    game.alphas_guesses[word] = word_votes
  
  if data.startswith("g:b_choice:"):
    word_idx = int(data.replace("g:b_choice:", ""))
    word = game.beta_choices[word_idx]
    word_votes = game.betas_guesses.get(word, 0)
    word_votes += 1
    game.betas_guesses[word] = word_votes
  
    
  if session.game_substate == VoteWordsSubstate.RESULT:
    game.sessions_ready += 1
    if game.sessions_ready < len(game.chat_ids):
      await edit_message(session, "Waiting for other players to finish voting...")
      return False
    else:    
      result_message = game.check_team_guess()
      text = f"{result_message}Now Let's see round results"
      buttons = [[InlineKeyboardButton("See Results", callback_data = "g:round_results")]]

      owner_session = get_session_of_owner(game = game)
      await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [owner_session.chat_id])
      await edit_message(owner_session, text, buttons)
      
      game.state = GameState.RESULTS
      set_all_substates(game, None)

      return False
    

# Something is horribly wrong.