from data.default_categories import default_categories
from data.modes import GameMode

class User:
  def __init__(self, id, username):
    self.id = id
    self.game_id = None
    self.username = username
    self.random_modes = [m for m in GameMode if m != GameMode.RANDOM]
    self.random_categories = [cat for cat in default_categories]
    self.generated_categories = []
    self.least_random = 4

  def set_least_random(self):
    if len(self.random_modes) < 2:
      self.least_random = 4

    min_vals = sorted(m.min_players for m in self.random_modes)
    self.least_random = min_vals[1]