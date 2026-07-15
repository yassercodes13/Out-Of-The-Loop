import asyncio
from data.modes import GameMode
from data.default_categories import default_categories
from db.engine import get_session
from db.models import UserORM
from db.models.category_orm import category_to_orm
from db.models.user_orm import user_from_orm, user_to_orm
from models.user import User
from models.category import Category

async def main():
  async with get_session() as session:
    cat_1 = Category(
      title = "uc1",
      words = ["w1", "w2", "w3", "w3", "w4", "w5", "w6", "w7", "w8", "w9", "w10", "w11", "w12", "w13"],
      description = "test cat 1",
      language = "en",
      is_builtin = False,
      owner_id = 100,
    )
    cat_2 = Category(
      title = "uc2",
      words = ["ك1", "ك2", "ك3", "ك3", "ك4", "ك5", "ك6", "ك7", "ك8", "ك9", "ك10", "ك11", "ك12", "ك13"],
      description = "test cat 1",
      language = "ar",
      is_builtin = False,
      owner_id = 100,
    )

    user = User(
      id = 100,
      username = "testuser7",
      lang = "en",
      random_modes = [GameMode.SPY, GameMode.DOUBLE_BLUFF],
      generated_categories = [cat_1, cat_2],
      random_categories = [cat for cat in default_categories if cat.title == "Animals"] + [cat_2]             
    )

    user_from_db = await session.get(UserORM, 100)

    if user_from_db:
      await session.delete(user_from_db)

    user_orm = user_to_orm(user)

    session.add(user_orm)

    print(user_orm.__str__)

  async with get_session() as session:
    user_orm = await session.get(UserORM, 100)

    user = user_from_orm(user_orm)

    print(user.id, user.username, user.lang)
    print([m.name for m in user.random_modes])
    print([c.title for c in user.random_categories])
    print([c.title for c in user.generated_categories])
    print([w for w in [c.words for c in user.generated_categories ]])

asyncio.run(main())