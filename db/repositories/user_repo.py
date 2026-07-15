from db.models.user_orm import user_from_orm, user_to_orm
from db.engine import get_session
from models.user import User
from db.models import UserORM

async def get_user_by_id(id: int) -> User | None:
  async with get_session() as session:
    user_orm = await session.get(UserORM, id)
    user = None
    if user_orm:
      user = user_from_orm(user_orm)
    
    return user
  
async def add_user(user: User) -> User | None:
  async with get_session() as session:
    if await session.get(UserORM, user.id):
      return user
    
    user_orm = user_to_orm(user)
    session.add(user_orm)

    return user_from_orm(user_orm)


async def update_user(user: User) -> User | None:
  async with get_session() as session:
    user_orm = await session.get(UserORM, user.id)
    
    user_orm.lang = user.lang
    user_orm.username = user.username
    user_orm.random_modes_names = [m.name for m in user.random_modes]
    user_orm.random_categories_ids = [c.id for c in user.random_categories]

    return user_from_orm(user_orm)

async def delete_user(id: int) -> User | None:
  async with get_session() as session:
    user_orm = await session.get(UserORM, id)
    if user_orm:
      await session.delete(user_orm)