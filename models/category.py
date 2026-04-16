from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone


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

  @property
  def size(self):
    return len(self.words)
  
  def generate_id(self):
    timestamp = int(self.created_at.timestamp() * 1000)  # Convert to milliseconds
    self.id = f"{self.title.lower().replace(' ', '_')}_{timestamp}"
  
