from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class User(Base):

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_name: Mapped[str] = mapped_column(index=True, nullable=False)
    password : Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Mapped: This attribute is mapped to a database column, and its Python type is uuid
    # id: Mapped[UUID] = mapped_column(     # mapped_column(...) → Defines the column details
    #     PGUUID(as_uuid=True),  # Stores UUIDs in Postgres, returns them as Python uuid.UUID objects.
    #     primary_key=True,  # Marks this column as the unique identifier.
    #     default=uuid4,  # Automatically generates a new UUID when a row is inserted.
    # )


class Conversation(Base):

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True,default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),index=True,nullable=False)
    title: Mapped[str | None] = mapped_column(String(255),nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())     # Default UTC
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),)


class Message(Base):

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True,default=uuid4,)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),ForeignKey("conversations.id"),index=True,nullable=False,)
    role: Mapped[str] = mapped_column(String(20),nullable=False,)
    content: Mapped[str] = mapped_column(Text,nullable=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),index=True,)