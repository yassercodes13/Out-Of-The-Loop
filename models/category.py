from dataclasses import dataclass, field
import secrets
from typing import List, Optional
from datetime import datetime, timezone
from config import ID_ALPHABET, CATEGORY_CODE_LENGTH


@dataclass
class Category:
  title: str
  words: List[str]

  description: str = ""
  language: str = "en"

  is_builtin: bool = False
  id: Optional[str] = None
  owner_id: Optional[int] = None

  created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

  def __post_init__(self):
    if not self.id:
      self.generate_id()

  @property
  def size(self):
    return len(self.words)
  
  def generate_id(self):
    timestamp = int(self.created_at.timestamp() * 1000)  # in milliseconds
    rear_part = str(timestamp)[-4:]
    code = ''.join(secrets.choice(ID_ALPHABET) for _ in range(CATEGORY_CODE_LENGTH))
    self.id = f"{code}@{rear_part}"
  
