#runtime_manager.py
from data.runtime import *
from data.games import *
from data.users import *
from data.sessions import *


########################################
#                 Game                 #
########################################

def create_game(user_id: int, username: str):
  user = ensure_user(user_id = user_id, username = username)
  if user.game_id:
    terminate_game(game_id = user.game_id)
  
  game = make_game(owner_id = user_id)
  user.game_id = game.id

  return game

def terminate_game(game: Game = None, game_id: str = None):
  if not game:
    if not game_id:
      return None
    
    game = get_game_by_id(game_id)
    if not game:
      return

  for cid in game.chat_ids:
    terminate_session(chat_id=cid)
  
  for user_id in game.user_ids:
    user = get_user_by_id(user_id)
    if user:
      user.game_id = None

  return active_games.pop(game.id)


def get_game_of_user(user: User = None, user_id: int = None, username: str = None):
  if not user:
    if not user_id or not username:
      return None
    user = ensure_user(user_id = user_id, username = username)
  
  if user.game_id:
    return active_games.get(user.game_id)
  
  return None

def get_game_of_session(session: Session = None, chat_id: int = None):
  if not session:
    if not chat_id:
      return None
    session = active_sessions.get(chat_id)
  
  if session and session.game_id:
    return active_games.get(session.game_id)
  
  return None


########################################
#                 User                 #
########################################

def ensure_user(user_id, username):
  user = get_user_by_id(user_id)
  if not user:
    user = make_user(id = user_id, username = username)
  return user

def add_user_to_game(user: User, game: Game):
  user.game_id = game.id
  if user.id not in game.user_ids:
    game.user_ids.append(user.id)


#######################################
#               Session               #
#######################################

def set_session(chat_id: int, message_id: int, game_id: str, user_id: int, bot, game_substate = None):
  old_session = active_sessions.get(chat_id)
  if old_session:
    terminate_session(old_session)
  
  new_session = make_session(chat_id, message_id, game_id, user_id, bot, game_substate)

  game = get_game_by_id(game_id)
  if game:
    if new_session.chat_id not in game.chat_ids:
      game.chat_ids.append(new_session.chat_id)
  
  return new_session

def terminate_session(session: Session = None, chat_id: int = None):
  if not session:
    if not chat_id:
      return
    session = active_sessions.pop(chat_id, None)
  else:
    active_sessions.pop(session.chat_id, None)
  
  if session:
    game = get_game_by_id(session.game_id)
    if game and session.chat_id in game.chat_ids:
      game.chat_ids.remove(session.chat_id)
      return session

  

def get_session_of_owner(game: Game = None, game_id: str = None):
  if not game:
    if not game_id:
      return None
    game = get_game_by_id(game_id)
  
  if game and game.owner_id:
    for cid in game.chat_ids:
      session = active_sessions.get(cid)
      if session and session.user_id == game.owner_id:
        return session
      
  return None

def get_session_of_user(user_id, username):
  game = get_game_of_user(user_id = user_id, username = username)
  if game:
    for cid in game.chat_ids:
      session = active_sessions.get(cid)
      if session and session.user_id == user_id:
        return session
      
  return None

def get_all_sessions(game: Game = None, game_id: str = None, excluded: list[int] = None) -> list[Session]:
  excluded = excluded or []
  
  if not game:
    if not game_id:
      return []
    game = get_game_by_id(game_id)
  
  sessions = []
  if game:
    for cid in game.chat_ids:
      if cid in excluded:
        continue

      session = get_session_of_chat(cid)
      if session:
        sessions.append(session)
  
  return sessions


def ensure_session(chat_id: int, message_id: int, game_id: str, user_id: int, bot):
  session = get_session_of_chat(chat_id)
  if not session:
    session = set_session(chat_id, message_id, game_id, user_id, bot)
  return session