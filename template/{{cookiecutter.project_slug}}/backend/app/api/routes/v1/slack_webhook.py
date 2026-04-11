{%- if cookiecutter.use_slack %}
"""Slack Events API webhook endpoint.

Handles:
- URL verification challenge (Slack sends this when you configure the Request URL)
- Event callbacks (message, app_mention) — dispatched to ChannelMessageRouter

POST /slack/{bot_id}/events
"""

import asyncio
import logging
from typing import Any

{%- if cookiecutter.use_postgresql %}
from uuid import UUID
{%- endif %}

from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{bot_id}/events", status_code=200)
async def slack_events(
{%- if cookiecutter.use_postgresql %}
    bot_id: UUID,
{%- else %}
    bot_id: str,
{%- endif %}
    request: Request,
) -> Any:
    """Receive Slack Events API callbacks.

    Handles URL verification (challenge/response) and event dispatch.
    Returns HTTP 200 immediately to avoid Slack's 3s timeout, then
    processes the event asynchronously.
    """
    raw_body = (await request.body()).decode("utf-8")
    payload: dict[str, Any] = await request.json()

    # --- URL Verification Challenge ---
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    # --- Verify signature ---
    from app.channels import get_adapter
    from app.core.config import settings

    adapter = get_adapter("slack")

    headers = dict(request.headers)
    headers["_raw_body"] = raw_body  # needed for HMAC verification

    if settings.SLACK_SIGNING_SECRET:
        if not adapter.verify_webhook_signature(headers, settings.SLACK_SIGNING_SECRET):
            raise HTTPException(status_code=403, detail="Invalid Slack signature")

    # --- Load bot and check active ---
{%- if cookiecutter.use_postgresql %}
    from app.db.session import get_db_context
    from app.repositories import channel_bot_repo

    async with get_db_context() as db:
        bot = await channel_bot_repo.get_by_id(db, bot_id)
{%- elif cookiecutter.use_sqlite %}
    from contextlib import contextmanager

    from app.db.session import get_db_session
    from app.repositories import channel_bot_repo

    with contextmanager(get_db_session)() as db:
        bot = channel_bot_repo.get_by_id(db, str(bot_id))
{%- elif cookiecutter.use_mongodb %}
    from app.repositories import channel_bot_repo

    bot = await channel_bot_repo.get_by_id(str(bot_id))
{%- endif %}

    if not bot or not bot.is_active:
        return Response(status_code=200)

    # --- Parse event ---
    event = payload.get("event", {})
    if not event:
        return Response(status_code=200)

    incoming = adapter.parse_incoming(payload, str(bot_id))
    if incoming is None:
        return Response(status_code=200)  # ignore non-text events

    # Fire-and-forget — acknowledge to Slack immediately
    asyncio.create_task(_process_slack_event(incoming))
    return Response(status_code=200)


async def _process_slack_event(incoming: Any) -> None:
    """Process the Slack event asynchronously in the background."""
    from app.channels.router import ChannelMessageRouter

    router = ChannelMessageRouter()
    try:
{%- if cookiecutter.use_postgresql %}
        from app.db.session import get_db_context

        async with get_db_context() as db:
            await router.route(incoming, db)
{%- elif cookiecutter.use_sqlite %}
        from contextlib import contextmanager

        from app.db.session import get_db_session

        with contextmanager(get_db_session)() as db:
            await router.route(incoming, db)
{%- elif cookiecutter.use_mongodb %}
        await router.route(incoming, None)
{%- endif %}
    except Exception:
        logger.exception("Error processing Slack event")
{%- endif %}
