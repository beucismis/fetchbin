import random
from typing import Optional
from datetime import datetime

import shortuuid
from sqlmodel import SQLModel, Session, Field, create_engine

from . import models


sqlite_url = f"sqlite:///{models.Settings.DB_FILE}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


class FetchOutput(SQLModel, table=True):
    __tablename__ = "fetch_output"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field()
    public_id: str = Field(default_factory=shortuuid.uuid, unique=True, index=True)
    tool_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
