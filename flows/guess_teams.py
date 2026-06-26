from flows.msg_utils import *
from flows.states import GameState
from flows.substates import GuessTeamsSubstate
from telegram import InlineKeyboardButton, Update
from data.runtime_manager import get_session_of_owner
from texts import t, b

# --- screen renderers ---

async def render_detective_waiting_screen(game: Game, session: Session):
  await broadcast_message(
    game=game, mode="edit",
    text=t("detective_will_guess"),
    exclude_chat_ids=[session.chat_id]
  )
  buttons = [[InlineKeyboardButton(text="start", callback_data="g:start")]]
  await edit_message(session, t("your_turn_to_guess", detective_name=game.detective.name), buttons)


async def render_guessing_screen(session: Session, game: Game):
  detective = game.detective
  text = t("assign_teams")
  buttons = []

  for p in game.players:
    if p == detective:
      continue
    team = detective.team_guess[p.id]
    buttons.append([
      InlineKeyboardButton(
        t("player_team_toggle", p_name=p.name, team=team),
        callback_data=f"g:toggle_{p.id}"
      )
    ])

  buttons.append([InlineKeyboardButton(b("confirm"), callback_data="g:confirm_guess")])
  await edit_message(session, text, buttons)


async def render_result_screen(game: Game):
  result = game.check_detection()
  text = t(
    "guess_result",
    result=result,
    alphas=", ".join([p.name for p in game.alphas]),
    betas=", ".join([p.name for p in game.betas])
  )

  owner_session = get_session_of_owner(game=game)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
  buttons = [[InlineKeyboardButton(b("vote_words"), callback_data="g:vote_words")]]
  await edit_message(owner_session, text, buttons)


# --- dispatch ---

async def handle_guess_teams(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  detective = game.detective

  # --- START FLOW ---
  if data == "g:guess_teams" and session.game_substate is None:
    game.sessions_ready = 0

    detective.team_guess = {
      p.id: "A" for p in game.players if p != detective
    }

    session.game_substate = GuessTeamsSubstate.GUESSING
    set_all_substates(game, GuessTeamsSubstate.WAITING, exclude_chat_ids=[session.chat_id])

    await render_detective_waiting_screen(game, session)
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
    await render_result_screen(game)
    return False

  # --- RENDER GUESSING SCREEN (ONLY DETECTIVE) ---

  if session.game_substate == GuessTeamsSubstate.GUESSING:
    await render_guessing_screen(session, game)
    return False

  return False