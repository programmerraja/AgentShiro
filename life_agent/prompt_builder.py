import os
from .context import build_context_snapshot, BASE_DIR


def build_system_prompt() -> str:
    # Build or load context
    context = build_context_snapshot()

    prompt_path = os.path.join(BASE_DIR, "prompts", "agents", "daily-agent-v2.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # Replace placeholders
    # We do this after appending shared components since they also contain placeholders
    for placeholder, value in context.items():
        prompt_text = prompt_text.replace(placeholder, str(value))

    return prompt_text
