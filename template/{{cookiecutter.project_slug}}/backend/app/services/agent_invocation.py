{%- if cookiecutter.use_telegram or cookiecutter.use_slack %}
"""Framework-agnostic agent invocation for channel messages (non-streaming)."""

import logging
from typing import Any

{%- if cookiecutter.use_postgresql %}
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
{%- elif cookiecutter.use_sqlite %}
from sqlalchemy.orm import Session
{%- endif %}

from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentInvocationService:
    """Invoke the configured AI agent and return the final text response.

    Used by channel adapters where streaming is not required. Both the user
    message and the assistant reply are persisted to the database.
    """

{%- if cookiecutter.use_postgresql %}
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
{%- elif cookiecutter.use_sqlite %}
    def __init__(self, db: Session) -> None:
        self.db = db
{%- else %}
    def __init__(self) -> None:
        pass
{%- endif %}

    async def invoke(
        self,
        *,
        user_message: str,
{%- if cookiecutter.use_postgresql %}
        conversation_id: UUID,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
{%- else %}
        conversation_id: str,
        user_id: str | None = None,
        project_id: str | None = None,
{%- endif %}
        system_prompt_override: str | None = None,
        model_override: str | None = None,
    ) -> str:
        """Run the agent and return final text. Persists both messages to DB."""
        # 1. Persist user message
        await self._persist_user_message(conversation_id, user_message)

        # 2. Load history (excluding the message we just added to avoid duplication)
        history = await self._load_history(conversation_id)

        # 3. Call agent
        try:
            response_text = await self._call_agent(
                user_message=user_message,
                history=history,
                conversation_id=conversation_id,
                user_id=user_id,
                project_id=project_id,
                system_prompt_override=system_prompt_override,
                model_override=model_override,
            )
        except Exception as exc:
            logger.exception("Agent invocation failed: %s", exc)
            response_text = "Sorry, I encountered an error processing your request."

        # 4. Persist assistant message
        await self._persist_assistant_message(conversation_id, response_text)

        return response_text

    # -----------------------------------------------------------------------
    # Framework-specific agent calls
    # -----------------------------------------------------------------------

    async def _call_agent(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Dispatch to the framework-specific agent implementation."""
{%- if cookiecutter.use_pydantic_ai %}
        return await self._call_pydantic_ai(user_message=user_message, history=history, **kwargs)
{%- elif cookiecutter.use_pydantic_deep %}
        return await self._call_pydantic_deep(user_message=user_message, history=history, **kwargs)
{%- elif cookiecutter.use_langchain %}
        return await self._call_langchain(user_message=user_message, history=history, **kwargs)
{%- elif cookiecutter.use_langgraph %}
        return await self._call_langgraph(user_message=user_message, history=history, **kwargs)
{%- elif cookiecutter.use_crewai %}
        return await self._call_crewai(user_message=user_message, history=history, **kwargs)
{%- elif cookiecutter.use_deepagents %}
        return await self._call_deepagents(user_message=user_message, history=history, **kwargs)
{%- else %}
        # Fallback: echo the message (no agent configured)
        return f"Echo: {user_message}"
{%- endif %}

{%- if cookiecutter.use_pydantic_ai %}

    async def _call_pydantic_ai(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke PydanticAI agent (non-streaming)."""
        from app.agents.assistant import Deps, get_agent
        from app.api.routes.v1.agent import build_message_history

        model_name: str | None = kwargs.get("model_override")
        assistant = get_agent(model_name=model_name)

        model_history = build_message_history(history)
        deps = Deps()

        result = await assistant.agent.run(
            user_message,
            message_history=model_history,
            deps=deps,
        )
        return str(result.output)
{%- endif %}

{%- if cookiecutter.use_pydantic_deep %}

    async def _call_pydantic_deep(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke PydanticDeep agent (non-streaming).

        PydanticDeep manages its own conversation history via history_messages_path,
        so we pass the conversation_id for per-conversation persistence rather than
        replaying the DB message history.
        """
        from app.agents.pydantic_deep_assistant import PydanticDeepAssistant, PydanticDeepContext

        conversation_id = str(kwargs.get("conversation_id") or "default")
        user_id = str(kwargs.get("user_id")) if kwargs.get("user_id") else None
        model_name: str | None = kwargs.get("model_override")

        assistant = PydanticDeepAssistant(
            model_name=model_name,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        context = PydanticDeepContext(user_id=user_id)
        text, _, _ = await assistant.run(user_message, context=context)
        return text
{%- endif %}

{%- if cookiecutter.use_langchain %}

    async def _call_langchain(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke LangChain agent (async)."""
        from langchain_core.messages import AIMessage, HumanMessage

        from app.agents.langchain_assistant import get_agent

        assistant = get_agent()
        lc_history = self._build_langchain_history(history)
        lc_history.append(HumanMessage(content=user_message))

        result = await assistant.agent.ainvoke({"messages": lc_history})

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                content = msg.content
                return content if isinstance(content, str) else str(content)
        return ""

    def _build_langchain_history(self, history: list[dict[str, str]]) -> list[Any]:
        """Convert conversation history to LangChain message format."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_msgs: list[Any] = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lc_msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            elif role == "system":
                lc_msgs.append(SystemMessage(content=content))
        return lc_msgs
{%- endif %}

{%- if cookiecutter.use_langgraph %}

    async def _call_langgraph(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke LangGraph agent (async)."""
        from langchain_core.messages import AIMessage, HumanMessage

        from app.agents.langgraph_assistant import get_agent

        assistant = get_agent()
        lc_history = self._build_langchain_history(history)
        lc_history.append(HumanMessage(content=user_message))

        result = await assistant.graph.ainvoke({"messages": lc_history})

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                content = msg.content
                return content if isinstance(content, str) else str(content)
        return ""

    def _build_langchain_history(self, history: list[dict[str, str]]) -> list[Any]:
        """Convert conversation history to LangChain message format."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_msgs: list[Any] = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lc_msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            elif role == "system":
                lc_msgs.append(SystemMessage(content=content))
        return lc_msgs
{%- endif %}

{%- if cookiecutter.use_crewai %}

    async def _call_crewai(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke CrewAI crew (synchronous, run in thread executor)."""
        import asyncio

        from app.agents.crewai_assistant import get_agent

        assistant = get_agent()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: assistant.crew.kickoff(inputs={"question": user_message}),
        )
        return str(result)
{%- endif %}

{%- if cookiecutter.use_deepagents %}

    async def _call_deepagents(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Invoke DeepAgents graph (async)."""
        from langchain_core.messages import AIMessage, HumanMessage

        from app.agents.deepagents_assistant import get_agent

        assistant = get_agent()
        lc_history = self._build_langchain_history(history)
        lc_history.append(HumanMessage(content=user_message))

        result = await assistant.graph.ainvoke({"messages": lc_history})

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                content = msg.content
                return content if isinstance(content, str) else str(content)
        return ""

    def _build_langchain_history(self, history: list[dict[str, str]]) -> list[Any]:
        """Convert conversation history to LangChain/DeepAgents message format."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_msgs: list[Any] = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                lc_msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            elif role == "system":
                lc_msgs.append(SystemMessage(content=content))
        return lc_msgs
{%- endif %}

    # -----------------------------------------------------------------------
    # Persistence helpers
    # -----------------------------------------------------------------------

{%- if cookiecutter.use_postgresql %}
    async def _persist_user_message(self, conversation_id: UUID, content: str) -> None:
        """Persist the user message directly via conversation repo."""
        from app.repositories import conversation_repo

        await conversation_repo.create_message(
            self.db,
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    async def _persist_assistant_message(
        self, conversation_id: UUID, content: str
    ) -> None:
        """Persist the assistant reply directly via conversation repo."""
        from app.repositories import conversation_repo

        await conversation_repo.create_message(
            self.db,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            model_name=settings.AI_MODEL,
        )

    async def _load_history(
        self, conversation_id: UUID
    ) -> list[dict[str, str]]:
        """Load conversation message history ordered chronologically."""
        from app.repositories import conversation_repo

        messages = await conversation_repo.get_messages_by_conversation(
            self.db,
            conversation_id=conversation_id,
            skip=0,
            limit=200,
        )
        return [{"role": m.role, "content": m.content} for m in messages]

{%- elif cookiecutter.use_sqlite %}
    async def _persist_user_message(self, conversation_id: str, content: str) -> None:
        """Persist the user message directly via conversation repo (sync)."""
        from app.repositories import conversation_repo

        conversation_repo.create_message(
            self.db,
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    async def _persist_assistant_message(
        self, conversation_id: str, content: str
    ) -> None:
        """Persist the assistant reply directly via conversation repo (sync)."""
        from app.repositories import conversation_repo

        conversation_repo.create_message(
            self.db,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            model_name=settings.AI_MODEL,
        )

    async def _load_history(
        self, conversation_id: str
    ) -> list[dict[str, str]]:
        """Load conversation message history ordered chronologically (sync)."""
        from app.repositories import conversation_repo

        messages = conversation_repo.get_messages_by_conversation(
            self.db,
            conversation_id=conversation_id,
            skip=0,
            limit=200,
        )
        return [{"role": m.role, "content": m.content} for m in messages]

{%- elif cookiecutter.use_mongodb %}
    async def _persist_user_message(self, conversation_id: str, content: str) -> None:
        """Persist the user message directly via conversation repo (MongoDB)."""
        from app.repositories import conversation_repo

        await conversation_repo.create_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    async def _persist_assistant_message(
        self, conversation_id: str, content: str
    ) -> None:
        """Persist the assistant reply directly via conversation repo (MongoDB)."""
        from app.repositories import conversation_repo

        await conversation_repo.create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            model_name=settings.AI_MODEL,
        )

    async def _load_history(
        self, conversation_id: str
    ) -> list[dict[str, str]]:
        """Load conversation message history ordered chronologically (MongoDB)."""
        from app.repositories import conversation_repo

        messages = await conversation_repo.get_messages_by_conversation(
            conversation_id=conversation_id,
            skip=0,
            limit=200,
        )
        return [{"role": m.role, "content": m.content} for m in messages]

{%- else %}
    async def _persist_user_message(self, conversation_id: str, content: str) -> None:
        """No-op when no database is configured."""

    async def _persist_assistant_message(
        self, conversation_id: str, content: str
    ) -> None:
        """No-op when no database is configured."""

    async def _load_history(self, conversation_id: str) -> list[dict[str, str]]:
        """Return empty history when no database is configured."""
        return []
{%- endif %}
{%- endif %}
