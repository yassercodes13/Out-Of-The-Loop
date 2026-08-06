from typing import NamedTuple
from dataclasses import dataclass

class TextRef(NamedTuple):
  key : str
  kwargs : dict | None = None

class Button(NamedTuple):
  text : TextRef
  callback : str | None
  url: str | None = None

@dataclass
class Screen:
  textref: TextRef | list[TextRef]
  buttons: list[list[Button]] | None = None

@dataclass
class BroadcastScreens:
  special: Screen
  others: Screen