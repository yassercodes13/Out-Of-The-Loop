from models.game import Game
from models.session import Session
from data.modes import GameMode
from flows.states import GameState
from flows.substates import RevealSubstate
from telegram import InlineKeyboardButton, Update
from flows.msg_utils import *

async def handle_reveal(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:reveal" and session.game_substate is None:
    game.sessions_ready = 0
    set_all_substates(game, RevealSubstate.SHOW_RESULT)
  
  if session.game_substate == RevealSubstate.CHOICE:      # Branching
    set_all_substates(game, None)
    if data == "g:guess_outsider":
      game.state = GameState.GUESS_OUTSIDER
      return True
    elif data and data.startswith("g:guess_word:"):
      game.state = GameState.GUESS_WORD
      return True
    elif data == "g:vote_words":
      game.state = GameState.VOTE_WORDS
      return True
    elif data == "g:guess_teams":
      game.state = GameState.GUESS_TEAMS
      return True

    return False


  if session.game_substate == RevealSubstate.SHOW_RESULT:

    outsiders = game.outsiders
    
    if len(outsiders) == 1:
      text = f"{outsiders[0].name} was the outsider."
      buttons = [
        [InlineKeyboardButton("Guess Word", callback_data ="g:guess_word:0")]
      ]
      outsider_session = get_session_of_chat(outsiders[0].session_id)
      await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [outsider_session.chat_id])
      await edit_message(outsider_session, text, buttons)

      set_all_substates(game, RevealSubstate.CHOICE)
    
    elif len(outsiders) == 2:
      reveal_text = f"{outsiders[0].name} was the most voted outsider\n"
      choices_text = reveal_text + (
        f"{outsiders[0].name}, do you want to guess the word for 10 points or\n"
        "guess the other outsider for 20 points but -10 if wrong?"
      )

      buttons = [
        [InlineKeyboardButton("Guess Word", callback_data = "g:guess_word:0")],
        [InlineKeyboardButton("Guess Outsider", callback_data= "g:guess_outsider")]
      ]

      outsider_session = get_session_of_chat(outsiders[0].session_id)
      await broadcast_message(game = game, mode = "edit", text = reveal_text, exclude_chat_ids = [outsider_session.chat_id])
      await edit_message(outsider_session, choices_text, buttons)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False

    elif game.mode == GameMode.TEAMS and game.detective:
      text = f"Detective was {game.detective.name}!\n"
      buttons = [
        [InlineKeyboardButton("Guess Team Members", callback_data = "g:guess_teams")]
      ]

      detective_session = get_session_of_chat(game.detective.session_id)
      await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [detective_session.chat_id])
      await edit_message(detective_session, text, buttons)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False
      
    elif game.mode == GameMode.TEAMS and not game.detective:
      text = f"Team Alpha was {', '.join([p.name for p in game.alphas])}\nTeam Beta was {', '.join([p.name for p in game.betas])}"
      buttons = [
        [InlineKeyboardButton("Vote Words", callback_data="g:vote_words")]
      ]

      owner_session = get_session_of_owner(game=game)
      await broadcast_message(game = game, mode = "edit", text = text, exclude_chat_ids = [owner_session.chat_id])
      await edit_message(owner_session, text, buttons)
      set_all_substates(game, RevealSubstate.CHOICE)
      return False

    return False
  