"""Tool schemas for exobrain-tool plugin."""

BRAIN_THINK = {
    "name": "brain_think",
    "description": (
        "Create a structured plan for coding tasks using the reasoning engine. "
        "Call this BEFORE any action tools (edit, bash, task). "
        "The reasoning engine will return a step-by-step plan stored in "
        "~/.exobrain/state/plan.json. The gate will block action tools until a plan exists. "
        "Use this for non-trivial tasks that require planning."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The goal or task to plan for. Be specific.",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for plan isolation across threads.",
            },
        },
        "required": ["prompt"],
    },
}

BRAIN_PLAN_DONE = {
    "name": "brain_plan_done",
    "description": (
        "Mark the current plan step as done. Call this AFTER completing an action "
        "(file edit, test run, etc.) to advance to the next step. "
        "One word, one click — no arguments needed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID for plan isolation across threads.",
            },
        },
    },
}

BRAIN_PLAN_BLOCK = {
    "name": "brain_plan_block",
    "description": (
        "Mark the current plan step as blocked. Use when a step cannot proceed "
        "due to missing information or dependencies."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why is this step blocked?",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for plan isolation across threads.",
            },
        },
    },
}

BRAIN_PLAN_STATUS = {
    "name": "brain_plan_status",
    "description": (
        "Show the current plan status. Returns step progress, current step title, and total steps."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID for plan isolation across threads.",
            },
        },
    },
}
