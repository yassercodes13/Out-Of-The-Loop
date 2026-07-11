from enum import Enum

class Role(str, Enum):
  INSIDER = "insider"
  OUTSIDER = "outsider"
  SPY = "spy"
  ALPHA = "alpha"
  BETA = "beta"
  DETECTIVE = "detective"