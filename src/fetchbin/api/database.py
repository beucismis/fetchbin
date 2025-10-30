from datetime import datetime, timezone
from typing import Optional

import shortuuid
from sqlmodel import Field, Session, SQLModel, create_engine

from . import models

sqlite_url = f"sqlite:///{models.Settings.DB_FILE}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db_session():
    with Session(engine) as session:
        yield session


class FetchOutput(SQLModel, table=True):
    __tablename__ = "fetch_output"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field()
    public_id: str = Field(default_factory=shortuuid.uuid, unique=True, index=True)
    command: Optional[str] = Field(default=None)
    is_hidden: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    delete_token: str = Field(default_factory=shortuuid.uuid, unique=True, index=True)
    upvotes: int = Field(default=0)
    downvotes: int = Field(default=0)


class Vote(SQLModel, table=True):
    __tablename__ = "vote"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    share_id: int = Field(foreign_key="fetch_output.id", index=True)
    ip_address: str = Field(max_length=45, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
