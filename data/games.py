#games.py
import time
import random
import secrets
from data.runtime import *
from config import GAME_ID_ALPHABET, GAME_ID_LENGTH
  
def make_game(owner_id: int):
  game_id = generate_game_id(GAME_ID_LENGTH)
  game = Game(game_id, owner_id)
  add_game(game)
  return game

def add_game(game: Game):
  active_games[game.id] = game

def get_game_by_id(game_id: str):
  game = active_games.get(game_id, None)
  return game

def delete_game(game: Game):
  return active_games.pop(game.id, None)

def generate_game_id(length = GAME_ID_LENGTH):
  while True:
    game_id = ''.join(secrets.choice(GAME_ID_ALPHABET) for _ in range(length))
    if game_id not in active_games:
      return game_id