from flows.msg_utils import *
from flows.states import GameState
from flows.substates import VoteWordsSubstate
from telegram import InlineKeyboardButton, Update
from data.runtime_manager import get_session_of_owner
from models.player import Player
from texts import t, b


# --- screen renderers ---

async def render_vote_words_start_screen(game: Game):
  await broadcast_message(
    game=game, mode="edit",
    text=t("vote_words_intro"),
    buttons=[[InlineKeyboardButton(b("start_voting"), callback_data="g:start_voting")]]
  )


async def render_voting_screen(session: Session, voter: Player, other_team: str, choices: list, prefix: str):
  text = t("vote_prompt", voter_name = voter.name, other_team=other_team)
  buttons = [
    [InlineKeyboardButton(choice, callback_data = f"g:{prefix}_choice:{i}")]
    for i, choice in enumerate(choices)
  ]
  await edit_message(session, text, buttons)


async def render_waiting_result_screen(session: Session):
  await edit_message(session, t("waiting_voting"))


async def render_vote_result_screen(game: Game):
  result_message = game.check_team_guess()
  text = t("see_results_prompt", result_message = result_message)
  buttons = [[InlineKeyboardButton(b("see_results"), callback_data="g:round_results")]]

  owner_session = get_session_of_owner(game=game)
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
  await edit_message(owner_session, text, buttons)


# --- dispatch ---

async def handle_vote_words(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:vote_words" and session.game_substate is None:
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteWordsSubstate.START)
    await render_vote_words_start_screen(game)

  if (data == "g:start_voting" and session.game_substate == VoteWordsSubstate.START) or (session.game_substate == VoteWordsSubstate.VOTING and "_choice" in query.data):

    if session.turn_index >= len(session.players):
      session.game_substate = VoteWordsSubstate.RESULT
      vote = False
    else:
      voter = session.players[session.turn_index]
      vote = True

    if vote and voter == game.detective:
      session.turn_index += 1
      if session.turn_index >= len(session.players):
        vote = False
        session.game_substate = VoteWordsSubstate.RESULT
      else:
        voter = session.players[session.turn_index]

    if vote:
      session.game_substate = VoteWordsSubstate.VOTING

      if voter in game.alphas:
        choices = game.alpha_choices
        other_team = t("beta")
        prefix = "a"
      elif voter in game.betas:
        choices = game.beta_choices
        other_team = t("alpha")
        prefix = "b"
      else:
        return False  # Should never happen

      await render_voting_screen(session, voter, other_team, choices, prefix)
      session.turn_index += 1

  if data.startswith("g:a_choice:"):
    word_idx = int(data.replace("g:a_choice:", ""))
    word = game.alpha_choices[word_idx]
    game.alphas_guesses[word] = game.alphas_guesses.get(word, 0) + 1

  if data.startswith("g:b_choice:"):
    word_idx = int(data.replace("g:b_choice:", ""))
    word = game.beta_choices[word_idx]
    game.betas_guesses[word] = game.betas_guesses.get(word, 0) + 1

  if session.game_substate == VoteWordsSubstate.RESULT:
    game.sessions_ready += 1
    if game.sessions_ready < len(game.chat_ids):
      await render_waiting_result_screen(session)
      return False
    else:
      await render_vote_result_screen(game)
      game.state = GameState.RESULTS
      set_all_substates(game, None)
      return False

  return False