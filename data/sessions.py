from models.session import Session
from data.runtime import active_sessions

def make_session(id: int, message_id: int, user_id: int, bot, job_queue, game_id: str | None = None, game_substate: str | None = None):
  session = Session(id = id, message_id = message_id, user_id = user_id, bot = bot, job_queue = job_queue, game_id = game_id, game_substate = game_substate)
  add_session(session)
  return session

def add_session(session: Session):
  active_sessions[session.id] = session

def get_session_by_id(id: int):
  session = active_sessions.get(id, None)
  return session

def delete_session(session: Session):
  return active_sessions.pop(session.id, None)