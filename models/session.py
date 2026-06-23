from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Bot
from models.player import Player
class Session:
  def __init__(self, chat_id, message_id, game_id, user_id, bot, game_substate = None):
    self.chat_id = chat_id
    self.message_id = message_id
    self.game_id = game_id
    self.user_id = user_id
    self.game_substate = game_substate
    self.bot: Bot = bot
    self.players: list[Player] = []
    self.turn_index = 0
    self.ready = False
    self.text = None
    self.raw_markup = None
    self.parse_mode = None
    
  def set_ui(self, text:str = None, parse_mode:str = "", raw_markup:list = None, buttons: list[list[InlineKeyboardButton]]= None):
    self.text = text
    
    if raw_markup is not None:
      self.raw_markup = raw_markup
    else:
      self.raw_markup = []
    
    if buttons and raw_markup is None:
      for r in buttons:
        row = []
        for btn in r:
          row.append((btn.text, btn.callback_data))
        self.raw_markup.append(row)
    
    self.parse_mode = parse_mode

  def copy_ui(self, session: "Session"):
    self.text = session.text
    self.raw_markup = [row[:] for row in session.raw_markup]
    self.parse_mode = session.parse_mode

  
  def build_buttons(self):
    if not self.raw_markup:
      return None

    return [
      [InlineKeyboardButton(text, callback_data=data) for text, data in row]
      for row in self.raw_markup
    ]
  
  def build_markup(self):
    if not self.raw_markup:
      return None
    
    return InlineKeyboardMarkup(self.build_buttons())

  def prepare_players(self, names, game):
    self.players.extend(game.prepare_players(self.chat_id, names))
