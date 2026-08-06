from flows.utils import set_all_substates, reset_turn_indices
from flows.states import GameState
from flows.substates import VoteWordsSubstate
from telegram import Update
from data.links import get_session_of_owner
from adapters.telegram.messaging import edit_message, broadcast_message
from texts.refs import TextRef
from models import Game, Session
from views.vote_words import (
  render_vote_words_start_screen,
  render_voting_screen,
  render_waiting_screen,
  render_vote_result_screen,
)


async def handle_vote_words(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:vote_words" and session.game_substate is None:
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteWordsSubstate.START, set_waited=True)

    screen = render_vote_words_start_screen()
    await broadcast_message(game=game, mode="edit", text=screen.textref, buttons=screen.buttons)
    return False

  if (data == "g:start_voting" and session.game_substate == VoteWordsSubstate.START) or (
    session.game_substate == VoteWordsSubstate.VOTING and data and "_choice" in data
  ):

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
        other_team = TextRef("beta")
        prefix = "a"
      elif voter in game.betas:
        choices = game.beta_choices
        other_team = TextRef("alpha")
        prefix = "b"
      else:
        return False

      screen = render_voting_screen(voter.name, other_team, choices, prefix)
      await edit_message(session, screen.textref, screen.buttons)
      session.turn_index += 1
      return False

  # --- Handle vote submissions ---
  if data and data.startswith("g:a_choice:"):
    word_idx = int(data.replace("g:a_choice:", ""))
    word = game.alpha_choices[word_idx]
    game.alphas_guesses[word] = game.alphas_guesses.get(word, 0) + 1

  if data and data.startswith("g:b_choice:"):
    word_idx = int(data.replace("g:b_choice:", ""))
    word = game.beta_choices[word_idx]
    game.betas_guesses[word] = game.betas_guesses.get(word, 0) + 1

  # --- RESULT SCREEN ---
  if session.game_substate == VoteWordsSubstate.RESULT:
    game.sessions_ready += 1
    session.waited = False

    if game.sessions_ready < len(game.session_ids):
      screen = render_waiting_screen()
      await edit_message(session, screen.textref, screen.buttons)
      return False
    else:
      result = game.check_team_guess()
      screens = render_vote_result_screen(result)

      owner_session = get_session_of_owner(game=game)
      owner_session.waited = True

      await broadcast_message(
        game=game,
        mode="edit",
        text=screens.others.textref,
        exclude_session_ids=[owner_session.id]
      )

      await edit_message(owner_session, screens.special.textref, screens.special.buttons)

      game.state = GameState.RESULTS
      set_all_substates(game, None)
      return False

  return False