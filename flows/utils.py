from data.links import get_all_sessions
from models.session import Session
from models.game import Game

def set_all_substates(game: Game, substate, exclude_session_ids: list[int] = None, set_waited: bool = None):
  exclude_session_ids = exclude_session_ids or []
  sessions: list[Session] = get_all_sessions(game=game, excluded=exclude_session_ids)
  for session in sessions:
    session.game_substate = substate
    if set_waited is not None: session.waited = set_waited


def reset_turn_indices(game, exclude_session_ids: list[int] = None):
  exclude_session_ids = exclude_session_ids or []
  sessions = get_all_sessions(game=game, excluded=exclude_session_ids)
  for session in sessions:
    session.turn_index = 0


def empty_slots(game: Game):
  sessions_with_no_players = 0
  sessions = get_all_sessions(game=game)
  for s in sessions:
    if len(s.players) == 0:
      sessions_with_no_players += 1
  return game.initial_players_count - len(game.players) - sessions_with_no_players + 1