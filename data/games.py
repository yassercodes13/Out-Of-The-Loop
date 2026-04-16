#games.py
from data.runtime import *

def make_game(owner_id: int):
  game = Game(owner_id)
  add_game(game)
  return game

def add_game(game: Game):
  active_games[game.id] = game

def get_game_by_id(game_id: int):
  game = active_games.get(game_id, None)
  return game

def delete_game(game: Game):
  return active_games.pop(game.id, None)