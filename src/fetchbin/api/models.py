import os
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from sqlmodel import SQLModel


class Settings(BaseSettings):
    DATA_DIR: ClassVar[str] = os.environ.get("FETCHBIN_DATA_DIR", "data/")
    DB_FILE: ClassVar[str] = os.path.join(DATA_DIR, "app.db")


class ShareRequest(SQLModel):
    content: str = Field(max_length=1024 * 1024, description="Content to share (max 1MB)")
    command: str | None = Field(None, max_length=500, description="Command that generated the output")
    is_hidden: bool = False

    @validator("content")
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v

    @validator("command")
    def validate_command(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class HealthCheck(BaseModel):
    status: str = Field()
    version: str = Field()
    timestamp: datetime = Field()
