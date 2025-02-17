from datetime import datetime
from sqlmodel import Field, SQLModel


class AIGCResult(SQLModel):
    text: str
    images: dict[str, str]


class AIGCContent(SQLModel, table=True):
    __tablename__ = "aigc_content"

    id: int | None = Field(default=None, primary_key=True)
    text_content: str
    image_content: str
    retry: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
