from data.runtime_manager import *

# Still an idea.
class GameService:
  @staticmethod
  def join_game(user: User, game: Game):
    if user.id not in game.user_ids:
      game.user_ids.append(user.id)

    user.game_id = game.id

  @staticmethod
  def leave_game(user: User, game: Game):
    if user.id in game.user_ids:
      game.user_ids.remove(user.id)

    user.game_id = None

  @staticmethod
  def end_game(game: Game):
    # remove all users from game
    for uid in game.user_ids:
      user = get_user_by_id(uid)
      if user:
        user.game_id = None

    game.user_ids.clear()