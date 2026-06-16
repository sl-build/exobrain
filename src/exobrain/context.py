"""ExoBrain CLI — Context injection for think command."""

from __future__ import annotations

import sys
from pathlib import Path

from .errors import InputError


def build_context_block(
    context: str | None = None,
    context_file: str | None = None,
    stdin_context: bool = False,
    metadata: list[str] | None = None,
) -> str | None:
    """Build context block from various sources.

    Returns None if no context provided.
    Returns formatted string like:
        <context>
        ...content...
        key: value
        </context>
    """
    parts: list[str] = []

    # Inline context
    if context:
        parts.append(context.strip())

    # Context from file
    if context_file:
        path = Path(context_file)
        if not path.exists():
            raise InputError(f"Context file not found: {context_file}")
        try:
            parts.append(path.read_text().strip())
        except OSError as e:
            raise InputError(f"Cannot read context file {context_file}: {e}") from e

    # Context from stdin
    if stdin_context:
        if not sys.stdin.isatty():
            try:
                stdin_data = sys.stdin.read().strip()
                if stdin_data:
                    parts.append(stdin_data)
            except OSError as e:
                raise InputError(f"Cannot read from stdin: {e}") from e
        else:
            # If stdin is a tty (no pipe), skip silently
            pass

    # Metadata key=value pairs
    if metadata:
        meta_lines = []
        for item in metadata:
            if "=" not in item:
                raise InputError(f"Metadata must be KEY=VALUE, got: {item}")
            meta_lines.append(item)
        if meta_lines:
            parts.append("Metadata:\n" + "\n".join(f"  {m}" for m in meta_lines))

    if not parts:
        return None

    return "<context>\n" + "\n\n".join(parts) + "\n</context>"


def assemble_messages(
    prompt: str,
    context_block: str | None = None,
    system_prompt: str | None = None,
    raw: bool = False,
) -> list[dict]:
    """Assemble the messages list for the API call.

    Order: system_prompt → context_block → user prompt.
    """
    messages: list[dict] = []

    if not raw and system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Build user content: context + prompt
    user_parts: list[str] = []
    if context_block:
        user_parts.append(context_block)
    user_parts.append(prompt)

    user_content = "\n\n".join(user_parts)
    messages.append({"role": "user", "content": user_content})

    return messages
