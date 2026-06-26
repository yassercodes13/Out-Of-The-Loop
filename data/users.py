#users.py
from data.runtime import *

def make_user(id: int, username :str, lang: str = 'en'):
  user = User(id = id, username = username, lang = lang)
  add_user(user)
  return user

def add_user(user: User):
  active_users[user.id] = user

def get_user_by_id(user_id: int):
  user = active_users.get(user_id, None)
  return user

def delete_user(user: User):
  return active_users.pop(user.id, None)