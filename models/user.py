from data.default_categories import default_categories
from data.modes import GameMode
from models.category import Category

class User:
  def __init__(self, id, username, lang = 'en'):
    self.id = id
    self.game_id = None
    self.username = username
    self.lang = lang
    self.random_modes = [m for m in GameMode if m != GameMode.RANDOM]
    self.random_categories: list[Category] = [cat for cat in default_categories]
    self.generated_categories: list[Category] = []

  @property
  def min_players_for_random(self):
    min_vals = sorted(m.min_players for m in self.random_modes)
    return min_vals[1]