from data.runtime import *
from data.games import *
from data.users import *
from data.sessions import *

def link_user_and_game(user: User, game: Game):
  user.game_id = game.id
  if user.id not in game.user_ids:
    game.user_ids.append(user.id)

def link_session_and_game(session: Session, game: Game):
  session.game_id = game.id
  if session.id not in game.session_ids:
    game.session_ids.append(session.id)

def get_session_of_owner(game: Game = None):
  if not game:
    return None
   
  if game and game.owner_session_id:
    session = get_session_by_id(game.owner_session_id)
    return session
  
  return None

def get_game_of_session(session_id: int):
  if not session_id:
    return None
  session = get_session_by_id(session_id)

  if session and session.game_id:
    return get_game_by_id(session.game_id)
  
  return None

def get_all_sessions(game: Game = None, excluded: list[int] = None) -> list[Session]:
  excluded = excluded or []
  
  sessions = []
  
  if game:
    for sid in game.session_ids:
      if sid in excluded:
        continue

      session = get_session_by_id(sid)
      if session:
        sessions.append(session)
  
  return sessions
  
async def get_session_of_user(user_id: int):
  game = await get_game_of_user(user_id = user_id)
  if game:
    for sid in game.session_ids:
      session = get_session_by_id(sid)
      if session and session.user_id == user_id:
        return session
      
  return None

async def get_game_of_user(user_id: int):
  if not user_id:
    return None
  user = await get_user_by_id(user_id = user_id)
  
  if user and user.game_id:
    return get_game_by_id(user.game_id)
  
  return None