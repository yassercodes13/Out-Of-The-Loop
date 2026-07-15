#users.py
from data.runtime import *
from db.repositories import user_repo

async def make_user(id: int, username :str, lang: str = 'en'):
  user = User(id = id, username = username, lang = lang)
  await add_user(user)
  return user

async def add_user(user: User):
  if not user: return
  
  user = await user_repo.add_user(user)
  active_users[user.id] = user

async def get_user_by_id(user_id: int):
  user = active_users.get(user_id, None)
  if not user:
    user = await user_repo.get_user_by_id(user_id)
    if not user: return None
    active_users[user.id] = user

  return user

async def delete_user(user: User):
  if not user: return

  await user_repo.delete_user(user.id)
  return active_users.pop(user.id, None)

async def update_user(user: User):
  if not user: return
  user = await user_repo.update_user(user)
  if user:
    active_users[user.id] = user