from flows.msg_utils import *
from flows.states import GameState
from flows.substates import GuessTeamsSubstate
from telegram import InlineKeyboardButton, Update
from data.runtime_manager import get_session_of_owner


async def handle_guess_teams(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  detective = game.detective

  # --- START FLOW ---
  if data == "g:guess_teams" and session.game_substate is None:
    game.sessions_ready = 0

    # initialize guesses (only for detective session)
    detective.team_guess = {
      p.id: "A" for p in game.players if p !=   detective
    }

    session.game_substate = GuessTeamsSubstate.GUESSING
    buttons = [[InlineKeyboardButton(text = "start", callback_data = "g:start")]]
    # others just wait
    set_all_substates(
      game,
      GuessTeamsSubstate.WAITING,
      exclude_chat_ids=[session.chat_id]
    )

    await broadcast_message(
      game = game,
      mode = "edit",
      text = "The detective will now guess which team each player was in.",
      exclude_chat_ids = [session.chat_id]
    )
    await edit_message(session, f"Now you will guess the teams, {game.detective.name}", buttons)
    return False

  # --- TOGGLE PLAYER TEAM ---

  elif data and data.startswith("g:toggle_") and session.game_substate == GuessTeamsSubstate.GUESSING:
    player_id = int(data.replace("g:toggle_", ""))

    if player_id in detective.team_guess:
      current = detective.team_guess[player_id]
      detective.team_guess[player_id] = "B" if current == "A" else "A"

  # --- CONFIRM GUESS ---

  elif data == "g:confirm_guess" and session.game_substate == GuessTeamsSubstate.GUESSING:
    detective.sus_alphas = []
    detective.sus_betas = []

    for p in game.players:
      if p == detective:
        continue

      if detective.team_guess[p.id] == "A":
        detective.sus_alphas.append(p)
      else:
        detective.sus_betas.append(p)

    set_all_substates(game, GuessTeamsSubstate.RESULT)

  # --- MOVE TO NEXT PHASE ---

  elif data == "g:vote_words" and session.game_substate == GuessTeamsSubstate.RESULT:
    game.state = GameState.VOTE_WORDS
    set_all_substates(game, None)
    return True

  # --- RESULT SCREEN ---

  if session.game_substate == GuessTeamsSubstate.RESULT:
    result = game.check_detection()

    text = f"Detective got {result}\n"
    text += "Alpha team: " + ", ".join([p.name for p in game.alphas]) + "\n"
    text += "Beta team: " + ", ".join([p.name for p in game.betas]) + "\n"

    owner_session = get_session_of_owner(game=game)

    # others just see result
    await broadcast_message(
      game = game,
      mode = "edit",
      text = text,
      exclude_chat_ids=[owner_session.chat_id]
    )

    # detective gets button
    buttons = [[InlineKeyboardButton("Vote Words", callback_data="g:vote_words")]]
    await edit_message(owner_session, text, buttons)

    return False

  # --- RENDER GUESSING SCREEN (ONLY DETECTIVE) ---

  if session.game_substate == GuessTeamsSubstate.GUESSING:
    text = "Assign teams:\n\n"
    buttons = []

    for p in game.players:
      if p == detective:
        continue

      team = detective.team_guess[p.id]

      buttons.append([
        InlineKeyboardButton(
          f"{p.name} → {team} ?",
          callback_data=f"g:toggle_{p.id}"
        )
      ])

    buttons.append([
      InlineKeyboardButton("Confirm", callback_data="g:confirm_guess")
    ])

    await edit_message(session, text, buttons)

    return False

  return False