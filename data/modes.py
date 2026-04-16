from enum import Enum

class GameMode(Enum):
  CLASSIC = "Classic"
  DOUBLE_BLUFF = "Double bluff"
  SPY = "Spy"
  THREE_BODY_PROBLEM = "Three Body Problem"
  TEAMS = "Teams"
  RANDOM = "Random"

  def __init__(self, label):
    self.label = label

    # defaults
    self.min_players = 3
    self.num_outsiders = 0
    self.num_spies = 0

    # per-mode config
    if self.name == "CLASSIC":
      self.min_players = 3
      self.num_outsiders = 1

    elif self.name == "DOUBLE_BLUFF":
      self.min_players = 4
      self.num_outsiders = 2

    elif self.name == "SPY":
      self.min_players = 4
      self.num_outsiders = 1
      self.num_spies = 1

    elif self.name == "THREE_BODY_PROBLEM":
      self.min_players = 6
      self.num_outsiders = 2
      self.num_spies = 1

    elif self.name == "TEAMS":
      self.min_players = 4

    elif self.name == "RANDOM":
      self.min_players = 4