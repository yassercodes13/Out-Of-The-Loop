from texts.setup import SETUP_TEXTS
from texts.buttons import b

TEXTS = SETUP_TEXTS 

def t(key, lang="en", **kwargs):
  template = TEXTS[key][lang]
  return template.format(**kwargs) if kwargs else template