from models.session import Session
from data.runtime import active_sessions

def make_session(chat_id: int, message_id :str, game_id, user_id: int, bot, job_queue, game_substate = None):
  session = Session(chat_id = chat_id, message_id = message_id, game_id = game_id, user_id = user_id, bot = bot, job_queue = job_queue, game_substate = game_substate)
  add_session(session)
  return session

def add_session(session: Session):
  active_sessions[session.chat_id] = session

def get_session_of_chat(chat_id: int):
  session = active_sessions.get(chat_id, None)
  return session

def delete_session(session: Session):
  return active_sessions.pop(session.chat_id, None)