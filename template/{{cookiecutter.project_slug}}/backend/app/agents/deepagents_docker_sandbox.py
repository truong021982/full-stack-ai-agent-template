{%- if cookiecutter.use_deepagents %}
"""Docker sandbox backend for DeepAgents.

Provides an isolated Docker container execution environment for the DeepAgents
framework. Implements BaseSandbox from deepagents.backends.sandbox so the agent
can run all file-operation tools plus shell execution inside an isolated container.

Configuration via settings:
    DEEPAGENTS_DOCKER_IMAGE   — Docker image (default: python:3.12-slim)
    DEEPAGENTS_DOCKER_TIMEOUT — Default command timeout in seconds (default: 30)
    DEEPAGENTS_WORKSPACE_DIR  — Working directory inside the container (default: /workspace)

Usage:
    # Per-conversation sandbox (one container per session)
    sandbox = DeepAgentsDockerSandbox(
        image="python:3.12-slim",
        workspace="/workspace",
        container_name="deepagents-conv-<id>",  # reuse for same conversation
    )
    # Container starts lazily on first use
    # Call sandbox.cleanup() when done or use as context manager:
    #   with DeepAgentsDockerSandbox(...) as sandbox:
    #       ...
"""

import logging
import os
import subprocess
import tempfile
import uuid

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox

logger = logging.getLogger(__name__)

DEFAULT_DOCKER_TIMEOUT = 30
DEFAULT_DOCKER_IMAGE = "python:3.12-slim"
DEFAULT_DOCKER_WORKSPACE = "/workspace"


class DeepAgentsDockerSandbox(BaseSandbox):
    """Docker sandbox for DeepAgents agent execution.

    Runs agent file operations and shell commands in an isolated Docker
    container. The container starts lazily on first use and can be reused
    across multiple invocations within the same conversation session.

    Extends BaseSandbox from deepagents, which provides all file-operation
    tools (ls, read, write, edit, grep, glob) as shell commands via execute().
    Only execute(), id, upload_files(), and download_files() are implemented here.

    For production: pair with DEEPAGENTS_INTERRUPT_TOOLS to require human
    approval before any file writes or command execution.
    """

    def __init__(
        self,
        image: str = DEFAULT_DOCKER_IMAGE,
        workspace: str = DEFAULT_DOCKER_WORKSPACE,
        timeout: int = DEFAULT_DOCKER_TIMEOUT,
        container_name: str | None = None,
    ) -> None:
        """Initialize Docker sandbox.

        Args:
            image: Docker image for the container (e.g. "python:3.12-slim").
            workspace: Working directory inside the container.
            timeout: Default timeout in seconds for command execution.
            container_name: Container name — pass a stable ID (e.g. conversation_id)
                to reuse the same container across reconnects. Defaults to a
                random "deepagents-<hex8>" name.
        """
        self._image = image
        self._workspace = workspace
        self._timeout = timeout
        self._container_id: str | None = None
        self._name = container_name or f"deepagents-{uuid.uuid4().hex[:8]}"

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        """Unique identifier for this sandbox (Docker container name)."""
        return self._name

    # ── Container lifecycle ───────────────────────────────────────────────────

    def _start_container(self) -> None:
        """Start the Docker container (called lazily on first use)."""
        logger.info("Starting Docker sandbox %s (image: %s)", self._name, self._image)
        try:
            result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", self._name,
                    "-w", self._workspace,
                    self._image,
                    "tail", "-f", "/dev/null",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            self._container_id = result.stdout.strip()

            # Ensure working directory exists
            subprocess.run(
                ["docker", "exec", self._container_id, "mkdir", "-p", self._workspace],
                capture_output=True,
                timeout=10,
                check=False,
            )
            logger.info("Docker sandbox %s started: %s", self._name, self._container_id)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to start Docker sandbox {self._name}: {e.stderr}"
            ) from e

    @property
    def _cid(self) -> str:
        """Resolved container ID, starting the container if needed."""
        if self._container_id is None:
            self._start_container()
        return self._container_id  # type: ignore[return-value]

    def cleanup(self) -> None:
        """Stop and remove the Docker container."""
        if self._container_id is None:
            return
        name = self._name
        logger.info("Cleaning up Docker sandbox %s", name)
        try:
            subprocess.run(
                ["docker", "stop", name],
                capture_output=True,
                timeout=30,
                check=False,
            )
            subprocess.run(
                ["docker", "rm", name],
                capture_output=True,
                timeout=10,
                check=False,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to clean up Docker sandbox %s: %s", name, e)
        finally:
            self._container_id = None

    # ── BaseSandbox abstract methods ──────────────────────────────────────────

    def execute(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        """Execute a shell command inside the Docker container.

        Args:
            command: Shell command string, executed via ``sh -c``.
            timeout: Per-command timeout. Overrides the instance default.

        Returns:
            ExecuteResponse with output, exit_code, and truncated flag.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        try:
            result = subprocess.run(
                ["docker", "exec", self._cid, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )

            output_parts: list[str] = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                stderr_lines = result.stderr.strip().split("\n")
                output_parts.extend(f"[stderr] {line}" for line in stderr_lines)

            output = "\n".join(output_parts) if output_parts else "<no output>"

            truncated = False
            max_output = 100_000
            if len(output) > max_output:
                output = output[:max_output] + f"\n\n... Output truncated at {max_output} bytes."
                truncated = True

            if result.returncode != 0:
                output = f"{output.rstrip()}\n\nExit code: {result.returncode}"

            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=truncated,
            )

        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output=f"Error: Command timed out after {effective_timeout} seconds.",
                exit_code=124,
                truncated=False,
            )
        except Exception as e:  # noqa: BLE001
            return ExecuteResponse(
                output=f"Error executing command ({type(e).__name__}): {e}",
                exit_code=1,
                truncated=False,
            )

    def upload_files(
        self,
        files: list[tuple[str, bytes]],
    ) -> list[FileUploadResponse]:
        """Upload files to the Docker container via ``docker cp``.

        Args:
            files: List of ``(container_path, content_bytes)`` tuples.

        Returns:
            List of FileUploadResponse, one per file.
        """
        responses: list[FileUploadResponse] = []

        for path, content in files:
            tmp_path: str | None = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                # Ensure parent directory exists in container
                parent = os.path.dirname(path)
                if parent and parent != ".":
                    subprocess.run(
                        ["docker", "exec", self._cid, "mkdir", "-p", parent],
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )

                result = subprocess.run(
                    ["docker", "cp", tmp_path, f"{self._cid}:{path}"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )

                if result.returncode != 0:
                    logger.warning("Failed to upload %s: %s", path, result.stderr)
                    responses.append(FileUploadResponse(path=path, error="invalid_path"))
                else:
                    responses.append(FileUploadResponse(path=path, error=None))

            except Exception as e:  # noqa: BLE001
                logger.warning("Error uploading %s: %s", path, e)
                responses.append(FileUploadResponse(path=path, error="invalid_path"))
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return responses

    def download_files(
        self,
        paths: list[str],
    ) -> list[FileDownloadResponse]:
        """Download files from the Docker container via ``docker cp``.

        Args:
            paths: List of container file paths to download.

        Returns:
            List of FileDownloadResponse, one per path.
        """
        responses: list[FileDownloadResponse] = []

        for path in paths:
            tmp_path: str | None = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name

                result = subprocess.run(
                    ["docker", "cp", f"{self._cid}:{path}", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )

                if result.returncode != 0:
                    responses.append(
                        FileDownloadResponse(path=path, content=None, error="file_not_found")
                    )
                else:
                    with open(tmp_path, "rb") as f:
                        content = f.read()
                    responses.append(
                        FileDownloadResponse(path=path, content=content, error=None)
                    )

            except Exception as e:  # noqa: BLE001
                logger.warning("Error downloading %s: %s", path, e)
                responses.append(
                    FileDownloadResponse(path=path, content=None, error="file_not_found")
                )
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return responses

    # ── Context manager support ───────────────────────────────────────────────

    def __enter__(self) -> "DeepAgentsDockerSandbox":
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()

    def __del__(self) -> None:
        try:
            self.cleanup()
        except Exception:  # noqa: BLE001
            pass
{%- else %}
"""Docker sandbox — not configured (deepagents not selected)."""
{%- endif %}
