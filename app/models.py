from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Request:
    """Заявка в том виде, в котором её удобно отдавать в хендлеры."""

    id: int
    user_id: int
    username: str | None
    name: str
    phone: str
    comment: str
    created_at: datetime

    @property
    def short_comment(self) -> str:
        return self.comment if len(self.comment) <= 80 else self.comment[:77] + "..."
