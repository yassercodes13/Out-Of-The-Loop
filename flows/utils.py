from data.runtime_manager import *
from models.session import Session
from models.game import Game

def set_all_substates(game: Game, substate, exclude_chat_ids: list[int] = None):
  exclude_chat_ids = exclude_chat_ids or []
  sessions: list[Session] = get_all_sessions(game=game, excluded=exclude_chat_ids)
  for session in sessions:
    session.game_substate = substate


def reset_turn_indices(game, exclude_chat_ids: list[int] = None):
  exclude_chat_ids = exclude_chat_ids or []
  sessions = get_all_sessions(game=game, excluded=exclude_chat_ids)
  for session in sessions:
    session.turn_index = 0


def empty_slots(game: Game):
  sessions_with_no_players = 0
  for s in get_all_sessions(game=game):
    if len(s.players) == 0:
      sessions_with_no_players += 1
  return game.initial_players_count - len(game.players) - sessions_with_no_players + 1