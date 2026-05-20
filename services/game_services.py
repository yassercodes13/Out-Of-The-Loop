from data.runtime_manager import *
from flows.msg_utils import broadcast_message, empty_slots
from flows.substates import SetupSubstate
from handlers.utils import *

def leave_game(user: User, game: Game):
  if user.id in game.user_ids:
    game.user_ids.remove(user.id)

  user.game_id = None

def end_game(game: Game):
  # remove all users from game
  for uid in game.user_ids:
    user = get_user_by_id(uid)
    if user:
      user.game_id = None

  game.user_ids.clear()
