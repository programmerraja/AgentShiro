import os
from .context import build_context_snapshot, BASE_DIR


def build_system_prompt(agent_mode: str, model_name: str) -> str:
    # Build or load context
    context = build_context_snapshot(model_name)

    # Select main prompt file
    if agent_mode == "1":
        prompt_path = os.path.join(BASE_DIR, "prompts", "agents", "daily-agent-v2.md")
    elif agent_mode == "2":
        prompt_path = os.path.join(
            BASE_DIR, "prompts", "agents", "weekly-analyzer-v2.md"
        )
    elif agent_mode == "3":
        prompt_path = os.path.join(
            BASE_DIR, "prompts", "agents", "pattern-detector-v2.md"
        )
    else:
        raise ValueError("Invalid agent mode selected.")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # Append shared components as required by SYSTEM_GUIDE
    shared_files = [
        # "system-context.md",
        # "alignment-rules.md",
        # "error-handling.md"
    ]

    for shared in shared_files:
        shared_path = os.path.join(BASE_DIR, "prompts", "_shared", shared)
        if os.path.exists(shared_path):
            with open(shared_path, "r", encoding="utf-8") as f:
                prompt_text += f"\n\n{f.read()}"

    # Replace placeholders
    # We do this after appending shared components since they also contain placeholders
    for placeholder, value in context.items():
        prompt_text = prompt_text.replace(placeholder, str(value))

    return prompt_text
