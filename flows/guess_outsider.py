from flows.msg_utils import *
from flows.states import GameState
from flows.substates import GuessOutsiderSubstate
from telegram import InlineKeyboardButton, Update

async def handle_guess_outsider(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  guesser = game.outsiders[0]

  if data == "g:guess_outsider" and session.game_substate is None:
    session.game_substate = GuessOutsiderSubstate.CHOOSING
    set_all_substates(game, GuessOutsiderSubstate.WAITING, exclude_chat_ids = [session.chat_id])
    await broadcast_message(game = game, mode = "edit", text = f"Waiting for {guesser.name} to guess the other outsider", exclude_chat_ids = [session.chat_id])

    buttons = []
    for p in game.players:
      if p != guesser:
        buttons.append([
          InlineKeyboardButton(p.name, callback_data=f"g:suspect:{p.id}")
        ])
    
    text = f"{guesser.name}, Who is the other outsider?"
   
    await edit_message(session, text, buttons)
  
  elif data.startswith("g:suspect:") and session.game_substate == GuessOutsiderSubstate.CHOOSING:
    set_all_substates(game, GuessOutsiderSubstate.RESULT)
    suspect_id = int(query.data.split(":")[2])
    suspect = game.get_player_by_id(suspect_id)
    result = game.check_suspect(suspect)
    
    other_outsider = game.outsiders[1]
    wait_text = f"{other_outsider.name} will guess the word now."

    def build_text(result, name, wait_text = ""):
      if result:
        text = f"{name} guessed that {suspect.name} was the outsider and that was correct!"
      else:
        text = f"{name} guessed that {suspect.name} was the outsider and that was wrong!\n{other_outsider.name} was the other outsider."

      return f"{text}\n\n{wait_text}"

    buttons = [[InlineKeyboardButton("Guess Word", callback_data = "g:guess_word:1")]]

    other_outsider_session = get_session_of_chat(other_outsider.session_id)

    await broadcast_message(
      game = game,
      mode = "edit",
      text = build_text(result, guesser.name, wait_text),
      exclude_chat_ids = [session.chat_id, other_outsider_session.chat_id]
    )
    
    if session.chat_id != other_outsider_session.chat_id:
      await edit_message(session, build_text(result, "You", wait_text))
      await edit_message(other_outsider_session, build_text(result, guesser.name), buttons)
    else:
      await edit_message(session, build_text(result, "You", wait_text), buttons)

    game.state = GameState.GUESS_WORD
    set_all_substates(game, None)