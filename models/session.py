from telegram.ext import Job
from config import TIME_BEFORE_SESSION_CHECK
from models.player import Player
from telegram.ext import ContextTypes
from telegram import Bot

class Session:
  def __init__(self, chat_id, message_id, game_id, user_id, bot, job_queue, game_substate = None):
    self.chat_id = chat_id
    self.message_id = message_id
    self.game_id = game_id
    self.user_id = user_id
    self.bot: Bot = bot

    self.game_substate = game_substate
    self.players: list[Player] = []
    self.turn_index = 0
    self.ready = False
    
    self.interrupt_substate = None
    self.popup_message_id = None
    
    self.text = None
    self.raw_markup = None
    self.parse_mode = None

    self.job_queue = job_queue
    self._waited = False
    self.reminder: Job = None

  def set_ui(self, text:str = None, parse_mode:str = "", raw_markup:list = None, buttons: list[list] = None):
    self.text = text
    self.raw_markup = raw_markup if raw_markup is not None else []
    
    self.parse_mode = parse_mode

  def copy_ui(self, session: "Session"):
    self.text = session.text
    self.raw_markup = [row[:] for row in session.raw_markup]
    self.parse_mode = session.parse_mode

  def prepare_players(self, names, game):
    self.players.extend(game.prepare_players(self.chat_id, names))


  @property
  def waited(self):
    return self._waited

  @waited.setter
  def waited(self, value: bool):
    if value == self._waited:
      return  # no change, don't touch the timer

    self._waited = value

    if self.reminder:
      self.reminder.schedule_removal()
      self.reminder = None

    from adapters.telegram.jobs import reminder_callback
    
    if value and self.game_id:
      self.reminder = self.job_queue.run_once(
        callback = reminder_callback,
        chat_id=self.chat_id,
        when=TIME_BEFORE_SESSION_CHECK,
      )
  
  def set_reminder(self, context: ContextTypes.DEFAULT_TYPE):
    """Sets a Reminder/Job if None and Updates if Any Exists"""
    if self.reminder:
      self.reminder.schedule_removal()
    
    from adapters.telegram.jobs import reminder_callback
    if self.game_id and self.waited:
      self.reminder = context.job_queue.run_once(
        callback = reminder_callback,
        chat_id = self.chat_id,
        when = TIME_BEFORE_SESSION_CHECK,
      )