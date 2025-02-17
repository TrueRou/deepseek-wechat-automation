from datetime import datetime
from enum import IntEnum, auto
from sqlmodel import Field, SQLModel


class Uploaders(IntEnum):
    OFFIACCOUNT = auto()


class AIGCResult(SQLModel):
    text: str
    images: dict[str, str]


class UploaderCredential(SQLModel, table=True):
    __tablename__ = "uploader_credentials"

    uploader: Uploaders = Field(primary_key=True)
    username: str = Field(primary_key=True)
    password: str
    credential: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIGCContent(SQLModel, table=True):
    __tablename__ = "aigc_contents"

    id: int | None = Field(default=None, primary_key=True)
    text_content: str
    image_content: str
    retry: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
