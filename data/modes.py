from enum import Enum


class GameMode(Enum):
  CLASSIC = ("Classic", 3, 1, 0)
  DOUBLE_BLUFF = ("Double Bluff", 4, 2, 0)
  SPY = ("Spy", 4, 1, 1)
  THREE_BODY_PROBLEM = ("Three Body Problem", 6, 2, 1)
  TEAMS = ("Teams", 4, 0, 0)
  RANDOM = ("Random", 4, 0, 0)

  def __init__(self, label, min_players, outsiders, spies):
    self.label = label
    self.min_players = min_players
    self.num_outsiders = outsiders
    self.num_spies = spies