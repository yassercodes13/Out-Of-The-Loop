from typing import NamedTuple

class TextRef(NamedTuple):
  key : str
  kwargs : dict | None = None

class Button(NamedTuple):
  text : TextRef
  callback : str | None
  url: str | None = None