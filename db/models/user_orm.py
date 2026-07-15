from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from data.modes import GameMode
from db.base import Base
from typing import TYPE_CHECKING
from db.models.category_orm import category_from_orm, category_to_orm
from models.user import User
from data.default_categories import default_categories

if TYPE_CHECKING:
  from .category_orm import CategoryORM


class UserORM(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(primary_key=True)               # Telegram user id — no autoincrement needed
  username: Mapped[str] = mapped_column(String, nullable=False)
  lang: Mapped[str] = mapped_column(String, default="en")

  random_modes_names: Mapped[list[str]] = mapped_column(JSON, default=list)
  random_categories_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

  generated_categories: Mapped[list["CategoryORM"]] = relationship(back_populates = "owner", lazy="selectin")

def user_to_orm(user: User) -> UserORM | None:
  modes = [m.name for m in user.random_modes]
  categories = [c.id for c in user.random_categories]
  generated_categories = [category_to_orm(cat) for cat in user.generated_categories]
    
  user_orm = UserORM(
    id = user.id,
    username = user.username,
    lang = user.lang,
    random_modes_names = modes,
    random_categories_ids = categories,
    generated_categories = generated_categories,
  )

  return user_orm

def user_from_orm(user_orm: UserORM) -> User | None:
  modes = [GameMode[n] for n in user_orm.random_modes_names]
  categories = [category_from_orm(c) for c in user_orm.generated_categories]
  random_categories = [category for category in default_categories + categories if category.id in user_orm.random_categories_ids]

  user = User(
    id = user_orm.id,
    username = user_orm.username,
    lang = user_orm.lang,
    random_modes = modes,
    random_categories = random_categories,
    generated_categories = categories,
  )

  return user