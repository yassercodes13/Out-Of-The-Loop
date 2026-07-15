from data.default_categories import default_categories
from data.modes import GameMode
from models.category import Category

class User:
  def __init__(
    self,
    id,
    username,
    lang = 'en',
    random_modes = None,
    random_categories = None,
    generated_categories = None
  ):
    self.id = id
    self.game_id = None
    self.username: str = username
    self.lang: str = lang
    self.random_modes: list[GameMode] = random_modes if random_modes is not None else [m for m in GameMode if m != GameMode.RANDOM]
    self.random_categories: list[Category] = random_categories if random_categories is not None else [cat for cat in default_categories]
    self.generated_categories: list[Category] = generated_categories if generated_categories is not None else []

  @property
  def min_players_for_random(self):
    min_vals = sorted(m.min_players for m in self.random_modes)
    return min_vals[1]