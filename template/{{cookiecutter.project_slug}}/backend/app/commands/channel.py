{%- if cookiecutter.use_telegram or cookiecutter.use_slack %}
"""Channel management CLI commands.

Commands:
    channel-list-bots         — List all registered channel bots
    channel-add-bot           — Register a new channel bot
    channel-webhook-register  — Register webhook URL for a bot with Telegram
    channel-webhook-delete    — Remove webhook for a bot (switches to polling)
    channel-test-message      — Send a test message through a bot
"""

import asyncio

import click

from app.commands import command, error, info, success, warning


# channel-list-bots


@command("channel-list-bots", help="List all registered channel bots")
@click.option("--platform", "-p", default=None, help="Filter by platform (e.g. telegram)")
def channel_list_bots(platform: str | None) -> None:
    """List all channel bots stored in the database."""

    async def _run() -> None:
{%- if cookiecutter.use_postgresql %}
        from app.db.session import get_db_context
        from app.repositories import channel_bot_repo

        async with get_db_context() as db:
            bots = (
                await channel_bot_repo.get_by_platform(db, platform)
                if platform
                else await channel_bot_repo.list_all(db)
            )
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session
        from app.repositories import channel_bot_repo

        with contextmanager(get_db_session)() as db:
            bots = (
                channel_bot_repo.get_by_platform(db, platform)
                if platform
                else channel_bot_repo.list_all(db)
            )
{%- elif cookiecutter.use_mongodb %}
        from app.repositories import channel_bot_repo

        bots = (
            await channel_bot_repo.get_by_platform(platform)
            if platform
            else await channel_bot_repo.list_all()
        )
{%- else %}
        bots = []
{%- endif %}

        if not bots:
            info("No channel bots registered.")
            return

        info(f"{'ID':<38}  {'Platform':<12}  {'Name':<30}  {'Active'}")
        info("-" * 90)
        for bot in bots:
            active_flag = "yes" if bot.is_active else "no"
            info(f"{str(bot.id):<38}  {bot.platform:<12}  {bot.name:<30}  {active_flag}")

    asyncio.run(_run())


# channel-add-bot


@command("channel-add-bot", help="Register a new channel bot")
@click.option("--platform", required=True, type=click.Choice(["telegram"]), help="Platform name")
@click.option("--name", "-n", required=True, help="Bot display name")
@click.option("--token", "-t", required=True, help="Bot token (e.g. from BotFather)")
@click.option(
    "--mode",
    default="open",
    type=click.Choice(["open", "whitelist", "jwt_linked", "group_only"]),
    help="Access policy mode",
)
def channel_add_bot(platform: str, name: str, token: str, mode: str) -> None:
    """Encrypt the bot token and register the bot in the database."""
    from app.core.channel_crypto import encrypt_token

    async def _run() -> None:
        encrypted = encrypt_token(token)
        access_policy = {"mode": mode}

{%- if cookiecutter.use_postgresql %}
        from app.db.session import get_db_context
        from app.repositories import channel_bot_repo

        async with get_db_context() as db:
            bot = await channel_bot_repo.create(
                db,
                platform=platform,
                name=name,
                token_encrypted=encrypted,
                access_policy=access_policy,
            )
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session
        from app.repositories import channel_bot_repo

        with contextmanager(get_db_session)() as db:
            bot = channel_bot_repo.create(
                db,
                platform=platform,
                name=name,
                token_encrypted=encrypted,
                access_policy=access_policy,
            )
{%- elif cookiecutter.use_mongodb %}
        from app.repositories import channel_bot_repo

        bot = await channel_bot_repo.create(
            platform=platform,
            name=name,
            token_encrypted=encrypted,
            access_policy=access_policy,
        )
{%- else %}
        bot = None
{%- endif %}

        if bot:
            success(f"Bot registered successfully! ID: {bot.id}")
            info(f"  Platform : {platform}")
            info(f"  Name     : {name}")
            info(f"  Mode     : {mode}")

    asyncio.run(_run())


# channel-webhook-register


@command("channel-webhook-register", help="Register webhook URL for a Telegram bot")
@click.option("--bot-id", required=True, help="Bot UUID")
def channel_webhook_register(bot_id: str) -> None:
    """Register the webhook URL for a bot with Telegram."""
    from app.core.config import settings

    async def _run() -> None:
        from app.channels import get_adapter
        from app.core.channel_crypto import decrypt_token

{%- if cookiecutter.use_postgresql %}
        from uuid import UUID

        from app.db.session import get_db_context
        from app.repositories import channel_bot_repo

        async with get_db_context() as db:
            bot = await channel_bot_repo.get_by_id(db, UUID(bot_id))
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session
        from app.repositories import channel_bot_repo

        with contextmanager(get_db_session)() as db:
            bot = channel_bot_repo.get_by_id(db, bot_id)
{%- elif cookiecutter.use_mongodb %}
        from app.repositories import channel_bot_repo

        bot = await channel_bot_repo.get_by_id(bot_id)
{%- else %}
        bot = None
{%- endif %}

        if not bot:
            error(f"Bot not found: {bot_id}")
            return

        adapter = get_adapter("telegram")
        token = decrypt_token(bot.token_encrypted)
        webhook_url = (
            f"{settings.TELEGRAM_WEBHOOK_BASE_URL}/api/v1/channels/telegram/{bot_id}/webhook"
        )

        info(f"Registering webhook: {webhook_url}")
        ok = await adapter.register_webhook(token, url=webhook_url, secret=bot.webhook_secret)
        if ok:
            success("Webhook registered successfully.")
        else:
            error("Failed to register webhook. Check logs for details.")

    asyncio.run(_run())


# channel-webhook-delete


@command("channel-webhook-delete", help="Remove webhook for a bot (switch to polling)")
@click.option("--bot-id", required=True, help="Bot UUID")
def channel_webhook_delete(bot_id: str) -> None:
    """Remove the webhook for a bot from Telegram."""

    async def _run() -> None:
        from app.channels import get_adapter
        from app.core.channel_crypto import decrypt_token

{%- if cookiecutter.use_postgresql %}
        from uuid import UUID

        from app.db.session import get_db_context
        from app.repositories import channel_bot_repo

        async with get_db_context() as db:
            bot = await channel_bot_repo.get_by_id(db, UUID(bot_id))
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session
        from app.repositories import channel_bot_repo

        with contextmanager(get_db_session)() as db:
            bot = channel_bot_repo.get_by_id(db, bot_id)
{%- elif cookiecutter.use_mongodb %}
        from app.repositories import channel_bot_repo

        bot = await channel_bot_repo.get_by_id(bot_id)
{%- else %}
        bot = None
{%- endif %}

        if not bot:
            error(f"Bot not found: {bot_id}")
            return

        adapter = get_adapter("telegram")
        token = decrypt_token(bot.token_encrypted)

        ok = await adapter.delete_webhook(token)
        if ok:
            success("Webhook removed. Bot is now in polling mode.")
        else:
            error("Failed to remove webhook. Check logs for details.")

    asyncio.run(_run())


# channel-test-message


@command("channel-test-message", help="Send a test message through a bot")
@click.option("--bot-id", required=True, help="Bot UUID")
@click.option("--chat-id", required=True, help="Telegram chat ID to send the message to")
@click.option("--text", default="Hello from your bot!", help="Message text")
def channel_test_message(bot_id: str, chat_id: str, text: str) -> None:
    """Send a test message to a chat via a registered bot."""

    async def _run() -> None:
        from app.channels import get_adapter
        from app.channels.base import OutgoingMessage
        from app.core.channel_crypto import decrypt_token

{%- if cookiecutter.use_postgresql %}
        from uuid import UUID

        from app.db.session import get_db_context
        from app.repositories import channel_bot_repo

        async with get_db_context() as db:
            bot = await channel_bot_repo.get_by_id(db, UUID(bot_id))
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session
        from app.repositories import channel_bot_repo

        with contextmanager(get_db_session)() as db:
            bot = channel_bot_repo.get_by_id(db, bot_id)
{%- elif cookiecutter.use_mongodb %}
        from app.repositories import channel_bot_repo

        bot = await channel_bot_repo.get_by_id(bot_id)
{%- else %}
        bot = None
{%- endif %}

        if not bot:
            error(f"Bot not found: {bot_id}")
            return

        adapter = get_adapter("telegram")
        token = decrypt_token(bot.token_encrypted)

        msg = OutgoingMessage(platform_chat_id=chat_id, text=text)
        info(f"Sending test message to chat {chat_id} via bot {bot.name}...")

        try:
            await adapter.send_message(token, msg)
            success("Message sent successfully.")
        except Exception as exc:
            error(f"Failed to send message: {exc}")

    asyncio.run(_run())
{%- endif %}
