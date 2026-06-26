from texts.setup import SETUP_TEXTS
from texts.inform import INFORM_TEXTS
from texts.question import QUESTION_TEXTS
from texts.vote import VOTE_TEXTS
from texts.reveal import REVEAL_TEXTS
from texts.vote_words import VOTE_WORDS_TEXTS
from texts.guess_word import GUESS_WORD_TEXTS
from texts.guess_teams import GUESS_TEAMS_TEXTS
from texts.guess_outsider import GUESS_OUTSIDER_TEXTS
from texts.results import RESULTS_TEXTS
from texts.mode_settings import MODE_SETTINGS_TEXTS
from texts.category_settings import CATEGORY_SETTINGS_TEXTS
from texts.general import GENERAL_TEXTS
from texts.buttons import b

_all_dicts = [
  SETUP_TEXTS, INFORM_TEXTS, QUESTION_TEXTS, VOTE_TEXTS,
  REVEAL_TEXTS, VOTE_WORDS_TEXTS, GUESS_WORD_TEXTS, GUESS_TEAMS_TEXTS,
  GUESS_OUTSIDER_TEXTS, MODE_SETTINGS_TEXTS, CATEGORY_SETTINGS_TEXTS, RESULTS_TEXTS, GENERAL_TEXTS
]
_all_keys = [k for d in _all_dicts for k in d]
assert len(_all_keys) == len(set(_all_keys)), \
  f"Duplicate text keys found: {[k for k in set(_all_keys) if _all_keys.count(k) > 1]}"

TEXTS = {**SETUP_TEXTS, **INFORM_TEXTS, **QUESTION_TEXTS, **VOTE_TEXTS, **REVEAL_TEXTS, **GUESS_WORD_TEXTS, **GUESS_TEAMS_TEXTS, **VOTE_WORDS_TEXTS, **GUESS_OUTSIDER_TEXTS, **MODE_SETTINGS_TEXTS, **CATEGORY_SETTINGS_TEXTS, **RESULTS_TEXTS, **GENERAL_TEXTS}

def t(key, lang="en", **kwargs):
  template = TEXTS[key][lang]
  return template.format(**kwargs) if kwargs else template