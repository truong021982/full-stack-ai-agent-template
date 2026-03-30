"""Message rating model for user feedback on AI responses."""

{%- if cookiecutter.use_postgresql and cookiecutter.use_sqlmodel %}
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from app.db.base import TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Message
    from app.db.models.user import User


class MessageRating(TimestampMixin, SQLModel, table=True):
    """User rating for AI assistant messages.

    Attributes:
        id: Unique rating identifier
        message_id: The message being rated (assistant messages only)
        user_id: The user who submitted the rating
        rating: 1 for like, -1 for dislike
        comment: Optional feedback comment
        created_at: When the rating was submitted
        updated_at: When the rating was last modified
    """

    __tablename__ = "message_ratings"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_user_rating"),
        CheckConstraint("rating IN (1, -1)", name="ck_rating_value"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    message_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
{%- if cookiecutter.use_jwt %}
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
{%- else %}
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
    )
{%- endif %}
    rating: int = Field(sa_column=Column(Integer, nullable=False))  # 1 or -1
    comment: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Relationships
    message: "Message" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MessageRating.message_id"}
    )
{%- if cookiecutter.use_jwt %}
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MessageRating.user_id"}
    )
{%- endif %}

    def __repr__(self) -> str:
        return f"<MessageRating(id={self.id}, rating={self.rating})>"


{%- elif cookiecutter.use_postgresql %}
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Message
    from app.db.models.user import User


class MessageRating(Base, TimestampMixin):
    """User rating for AI assistant messages."""

    __tablename__ = "message_ratings"

    # Unique constraint: one rating per user per message
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_user_rating"),
        CheckConstraint("rating IN (1, -1)", name="ck_rating_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
{%- if cookiecutter.use_jwt %}
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
{%- else %}
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
{%- endif %}
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or -1
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message",
        foreign_keys="MessageRating.message_id",
    )
{%- if cookiecutter.use_jwt %}
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="MessageRating.user_id",
    )
{%- endif %}

    def __repr__(self) -> str:
        return f"<MessageRating(id={self.id}, rating={self.rating})>"


{%- elif cookiecutter.use_sqlite and cookiecutter.use_sqlmodel %}
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.db.base import TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Message
{%- if cookiecutter.use_jwt %}
    from app.db.models.user import User
{%- endif %}


class MessageRating(TimestampMixin, SQLModel, table=True):
    """User rating for AI assistant messages.

    Attributes:
        id: Unique rating identifier
        message_id: The message being rated (assistant messages only)
        user_id: The user who submitted the rating
        rating: 1 for like, -1 for dislike
        comment: Optional feedback comment
        created_at: When the rating was submitted
        updated_at: When the rating was last modified
    """

    __tablename__ = "message_ratings"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_user_rating"),
        CheckConstraint("rating IN (1, -1)", name="ck_rating_value"),
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String(36), primary_key=True),
    )
    message_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
{%- if cookiecutter.use_jwt %}
    user_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
{%- else %}
    user_id: str = Field(
        sa_column=Column(
            String(36),
            nullable=False,
            index=True,
        ),
    )
{%- endif %}
    rating: int = Field(sa_column=Column(Integer, nullable=False))  # 1 or -1
    comment: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Relationships
    message: "Message" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MessageRating.message_id"}
    )
{%- if cookiecutter.use_jwt %}
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MessageRating.user_id"}
    )
{%- endif %}

    def __repr__(self) -> str:
        return f"<MessageRating(id={self.id}, rating={self.rating})>"


{%- elif cookiecutter.use_sqlite %}
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Message
{%- if cookiecutter.use_jwt %}
    from app.db.models.user import User
{%- endif %}


class MessageRating(Base, TimestampMixin):
    """User rating for AI assistant messages."""

    __tablename__ = "message_ratings"

    # Unique constraint: one rating per user per message
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_user_rating"),
        CheckConstraint("rating IN (1, -1)", name="ck_rating_value"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
{%- if cookiecutter.use_jwt %}
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
{%- else %}
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
{%- endif %}
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or -1
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message",
        foreign_keys="MessageRating.message_id",
    )
{%- if cookiecutter.use_jwt %}
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="MessageRating.user_id",
    )
{%- endif %}

    def __repr__(self) -> str:
        return f"<MessageRating(id={self.id}, rating={self.rating})>"


{%- elif cookiecutter.use_mongodb %}
from datetime import UTC, datetime
from typing import Optional

from beanie import Document, Link
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.schemas.message_rating import RatingValue


class MessageRating(Document):
    """User rating for AI assistant messages.

    Attributes:
        message_id: The message being rated (assistant messages only)
        conversation_id: The conversation containing the message (for validation)
        user_id: The user who submitted the rating
        rating: 1 for like, -1 for dislike
        comment: Optional feedback comment
        created_at: When the rating was submitted
        updated_at: When the rating was last modified
    """

    message_id: str
    conversation_id: str
{%- if cookiecutter.use_jwt %}
    user_id: str
{%- else %}
    user_id: str
{%- endif %}
    rating: RatingValue
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None

    class Settings:
        name = "message_ratings"
        indexes = [
            # Unique constraint: one rating per user per message (enforced)
            IndexModel([("message_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
            # Lookup by message
            "message_id",
            # Lookup by user
            "user_id",
            # Admin queries with date filtering
            IndexModel([("created_at", DESCENDING)]),
            # Conversation validation queries
            "conversation_id",
        ]


{%- else %}
"""Message rating models - not configured."""
{%- endif %}
