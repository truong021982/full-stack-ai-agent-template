{%- if cookiecutter.use_telegram or cookiecutter.use_slack %}
"""Base classes for channel adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IncomingMessage:
    """Normalised message from any messaging platform."""

    platform: str
    bot_id: str  # UUID str of the ChannelBot row
    platform_user_id: str
    platform_chat_id: str
    chat_type: str  # "private" | "group" | "supergroup" | "channel"
    text: str
    raw: dict[str, Any] = field(default_factory=dict)
    platform_username: str | None = None
    platform_display_name: str | None = None
    message_id: str | None = None


@dataclass
class OutgoingMessage:
    """Reply to send back to the platform."""

    platform_chat_id: str
    text: str
    parse_mode: str | None = None  # "Markdown" | "HTML" | None
    reply_to_message_id: str | None = None


class ChannelAdapter(ABC):
    """Abstract base class for all messaging platform adapters."""

    platform: str  # class-level constant e.g. "telegram"

    @abstractmethod
    async def send_message(self, bot_token: str, msg: OutgoingMessage) -> None:
        """Send a reply back to the platform."""

    @abstractmethod
    async def start_polling(self, bot_id: str, bot_token: str) -> None:
        """Start long-polling loop for this bot (dev mode)."""

    @abstractmethod
    async def stop_polling(self, bot_id: str) -> None:
        """Stop polling for this bot."""

    @abstractmethod
    async def register_webhook(
        self, bot_token: str, url: str, secret: str | None
    ) -> bool:
        """Register webhook URL with the platform. Returns True on success."""

    @abstractmethod
    async def delete_webhook(self, bot_token: str) -> bool:
        """Remove webhook from the platform."""

    @abstractmethod
    def verify_webhook_signature(self, headers: dict[str, str], secret: str) -> bool:
        """Verify that a webhook request came from the platform."""

    @abstractmethod
    def parse_incoming(
        self, raw_payload: dict[str, Any], bot_id: str
    ) -> IncomingMessage | None:
        """Parse raw platform payload into IncomingMessage. Return None to ignore."""
{%- endif %}
