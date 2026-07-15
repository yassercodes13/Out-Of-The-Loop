from sqlalchemy import select
from db.engine import get_session
from db.models import CategoryORM
from db.models.category_orm import category_from_orm, category_to_orm
from models.category import Category


async def get_category_by_id(id: str) -> Category | None:
  async with get_session() as session:
    category_orm = await session.get(CategoryORM, id)
    category = None
    if category_orm:
      category = category_from_orm(category_orm)

    return category


async def get_categories_by_owner(owner_id: int) -> list[Category]:
  async with get_session() as session:
    stmt = select(CategoryORM).where(CategoryORM.owner_id == owner_id)
    result = await session.execute(stmt)
    categories_orm = result.scalars().all()

    return [category_from_orm(c) for c in categories_orm]


async def add_category(category: Category) -> Category | None:
  async with get_session() as session:
    category_orm = category_to_orm(category)
    session.add(category_orm)
    return category_from_orm(category_orm)


async def update_category(category: Category) -> Category | None:
  async with get_session() as session:
    category_orm = await session.get(CategoryORM, category.id)
    if not category_orm:
      return None

    category_orm.title = category.title
    category_orm.words = category.words
    category_orm.description = category.description
    category_orm.language = category.language

    return category_from_orm(category_orm)


async def delete_category(id: str) -> None:
  async with get_session() as session:
    category_orm = await session.get(CategoryORM, id)
    if category_orm:
      await session.delete(category_orm)