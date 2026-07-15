from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from db.base import Base
from typing import TYPE_CHECKING
from models.category import Category

if TYPE_CHECKING:
  from .user_orm import UserORM

class CategoryORM(Base):
  __tablename__ = "categories"

  id: Mapped[str] = mapped_column(String, primary_key=True)
  title: Mapped[str] = mapped_column(String, nullable=False)
  words: Mapped[list[str]] = mapped_column(JSON, nullable=False)
  description: Mapped[str] = mapped_column(String, default="")
  language: Mapped[str] = mapped_column(String, default="en")
  is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
  owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
  owner: Mapped["UserORM | None"] = relationship(back_populates = "generated_categories")
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
  )

def category_to_orm(category: Category) -> CategoryORM | None:
  category_orm = CategoryORM(
    id = category.id,
    title = category.title,
    words = category.words,
    description = category.description,
    language = category.language,
    is_builtin = category.is_builtin,
    owner_id = category.owner_id,
    created_at = category.created_at,
  )
  return category_orm

def category_from_orm(category_orm: CategoryORM) -> Category:
  category = Category(
    id = category_orm.id,
    title = category_orm.title,
    words = category_orm.words,
    description = category_orm.description,
    language = category_orm.language,
    is_builtin = category_orm.is_builtin,
    owner_id = category_orm.owner_id,
    created_at = category_orm.created_at,
  )
  return category