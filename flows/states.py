from enum import Enum

class GameState(str, Enum):
  SETUP = "setup"
  INFORM = "inform"
  QUESTION = "question"
  VOTE = "vote"
  REVEAL = "reveal"
  GUESS_WORD = "guess_word"
  GUESS_OUTSIDER = "guess_outsider"
  VOTE_WORDS = "vote_words"
  GUESS_TEAMS = "guess_teams"
  RESULTS = "results"