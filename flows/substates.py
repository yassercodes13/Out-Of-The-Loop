from enum import Enum
from typing import Union

# ----------------------
# SETUP
# ----------------------
class SetupSubstate(str, Enum):
  PLAYERS_COUNT = "players_count"
  GAME_TYPE = "game_type"
  INPUT_NAMES = "input_names"
  WAITING = "waiting"                     # Waiting for other players to input their names (only for multiple phones mode)
  CHOOSE_ROUNDS = "choose_rounds"
  CHOOSE_CATEGORY = "choose_category"
  CREATE_CATEGORY = "create_category"
  CATEGORY_SETTINGS = "category_settings" 
  CHOOSE_MODE = "choose_mode"
  EDIT_RANDOM_MODE = "edit_random_mode"
  FINISHED = "finished"


# ----------------------
# INFORM
# ----------------------
class InformSubstate(str, Enum):
  SHOW = "show"                       # Player is viewing their info
  HIDE = "hide"                       # "Give phone to X"
  ROUND_INFO = "round_info"           # Shows the info of the entire round
  END = "end"


# ----------------------
# QUESTIOn
# ----------------------
class QuestionSubstate(str, Enum):
  ASK = "ask"                        # Main loop of asking
  END = "end"                        # Finished questioning (advance to voting)


# ----------------------
# VOTe
# ----------------------
class VoteSubstate(str, Enum):
  SELECT = "select"                  # Choosing who to vote
  CONFIRM = "confirm"                # Confirming vote
  END = "end"


# ----------------------
# REVEAL
# ----------------------
class RevealSubstate(str, Enum):
  SHOW_RESULT = "show_result"       # Show who outsider is
  CHOICE = "choice"                 # Choose next step (word / outsider)


# ----------------------
# GUESS WORD
# ----------------------
class GuessWordSubstate(str, Enum):
  CHOOSING  = "choosing"                    # Picking a word
  RESULT    = "result"                      # Showing correct/wrong
  WAITING   = "waiting"                     # Waiting for guesser to choose a word (while showing the guessing screen to others)


# ----------------------
# GUESS OUTSIDER
# ----------------------
class GuessOutsiderSubstate(str, Enum):
  CHOOSING = "choosing"            # Picking suspect
  RESULT = "result"                # Showing result
  WAITING = "waiting"


# ----------------------
# VOTE WORDS
# ----------------------
class VoteWordsSubstate(str, Enum):
  START = "start"                
  VOTING = "voting"            
  WAITING = "waiting"
  RESULT = "result"


# ----------------------
# GUESS TEAMS
# ----------------------
class GuessTeamsSubstate(str, Enum):
  GUESSING = "guessing"            
  RESULT = "result"     
  WAITING = "waiting"           


# ----------------------
# RESULTS
# ----------------------
class ResultsSubstate(str, Enum):
  ROUND_RESULTS = "round_results"                 # Round results screen
  ROUND_REPORT = "round_report"                   # Round report screen
  FINAL_RESULTS = "final_ersults"                 # End game results
  EDIT_SCORE = "edit_score"                       # Edit players scores


# ------------------
# Any Substate
# ------------------
AnySubstate = Union[
  SetupSubstate,
  InformSubstate,
  QuestionSubstate,
  VoteSubstate,
  RevealSubstate,
  GuessWordSubstate,
  GuessOutsiderSubstate,
  VoteWordsSubstate,
  GuessTeamsSubstate,
  ResultsSubstate
]