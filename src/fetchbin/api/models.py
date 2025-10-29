import os
from datetime import datetime
from typing import ClassVar

from sqlmodel import SQLModel
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATA_DIR: ClassVar[str] = os.environ.get("FETCHBIN_DATA_DIR", "data/")
    DB_FILE: ClassVar[str] = os.path.join(DATA_DIR, "app.db")


class HealthCheck(BaseModel):
    status: str = Field()
    timestamp: datetime = Field()


class ShareRequest(SQLModel):
    content: str
