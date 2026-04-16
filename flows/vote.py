from data.modes import GameMode
from flows.states import GameState
from flows.substates import VoteSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *

async def handle_voting(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data

  # --- INITIALIZE ---
  if data == 'g:start_vote':
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteSubstate.SELECT)
    buttons = [[InlineKeyboardButton(text = "Start Voting", callback_data = "g:revote")]]
    await broadcast_message(game = game, mode = "edit", text = session.text, buttons = buttons, exclude_chat_ids = [session.chat_id])
  
  elif data == 'g:revote':
    session.game_substate = VoteSubstate.SELECT

  elif data == "g:reveal" and session.game_substate == VoteSubstate.END:
    game.count_votes()
    game.state = GameState.REVEAL
    set_all_substates(game, None)
    return True

  # --- confirmation ---
  if data == "g:confirm" and session.game_substate == VoteSubstate.CONFIRM:
    voter = session.players[session.turn_index] 
    voter.confirm_vote()
    session.turn_index += 1
  
    session.game_substate = VoteSubstate.SELECT
  
    # --- END CONDITION ---

    if session.turn_index >= len(session.players):
      session.game_substate = VoteSubstate.END
      game.sessions_ready += 1
      ready = True if game.sessions_ready >= len(game.chat_ids) else False

      text = "Done Voting!"
      waiting_text = "\n\nWaiting for other players to vote."
      
      button_txt = "Reaveal Outsider"
      if game.mode == GameMode.TEAMS and game.detective:
        button_txt = "Reveal Detective"
      elif game.mode == GameMode.TEAMS:
        button_txt = "Reveal Teams"
        
      buttons = [[InlineKeyboardButton(button_txt, callback_data = "g:reveal")]]
      
      if session.user_id == game.owner_id and ready:
        await edit_message(session, text, buttons)
      else:
        text += waiting_text
        await edit_message(session, text)

        if ready:
          owner_session = get_session_of_owner(game=game)
          await edit_message(owner_session, text, buttons)

      return False



  # --- handle vote selection ---


  if data.startswith("g:vote_") and session.game_substate == VoteSubstate.SELECT:
    voter = session.players[session.turn_index]  
    voted_id = int(data.replace("g:vote_", ""))
    voted_player = game.get_player_by_id(voted_id)
    voter.vote_on(voted_player)

    session.game_substate = VoteSubstate.CONFIRM
    text=f"{voter.name}, are you sure you want to vote for {voted_player.name}?\n\nYou can't change this later."
    buttons = [
      [InlineKeyboardButton("Yes, confirm", callback_data = "g:confirm")],
      [InlineKeyboardButton("No, choose again", callback_data = "g:revote")]
    ]
    await edit_message(session, text, buttons)
    return False

  if session.game_substate == VoteSubstate.SELECT:
    # --- render current voter choices ---
    voter = session.players[session.turn_index] 
    buttons = []
    for p in game.players:
      if p != voter:
        buttons.append([InlineKeyboardButton(p.name, callback_data = f"g:vote_{p.id}")])

    if game.mode == GameMode.TEAMS:
      text = f"{voter.name}, vote for any of who you think are the in the other team:"
    else:
      text=f"{voter.name}, vote for who you think is the outsider:"
    
    await edit_message(session, text, buttons)
    
    return False