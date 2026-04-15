from life_agent.prompts import COMMON_TREE
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from agentshiro.agent import Agent
from agentshiro.loop import run_agent_loop
from life_agent.tools import (
    ReadFileTool,
    WriteFileTool,
    InsertFileTool,
)
from life_agent.storage import generate_daily_template
from life_agent.gamification import load_score
from life_agent.prompt_builder import build_system_prompt
from agentshiro.session import SessionManager
import argparse

COLOR_USER = "\033[92m"  # Green
COLOR_RESET = "\033[0m"
COLOR_SYSTEM = "\033[94m"  # Blue
COLOR_ERROR = "\033[91m"  # Red

model_name = "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:BF16"
model_name = "gpt-5.4-nano"
model_name = "LiquidAI/LFM2.5-1.2B-Thinking-GGUF:BF16"
model_name = "ollama/hf.co/unsloth/Phi-4-mini-instruct-GGUF:Q4_K_M"
model_name = "ollama/gemma4:e2b"
model_name = "ollama/qwen2.5:3b"
model_name = "anthropic/google/gemma4-4-e4b"
model_name = "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q5_K_M"
model_name = "anthropic/liquid/lfm2.5-1.2b"
model_name = "nvidia_nim/qwen/qwen3-next-80b-a3b-instruct"
# model_name = "nvidia_nim/minimaxai/minimax-m2.7"
# model_name = "nvidia_nim/nvidia/nemotron-mini-4b-instruct"


def main():
    parser = argparse.ArgumentParser(description="AgentShiro Life Assistant")
    parser.add_argument(
        "--list-sessions", action="store_true", help="List all available sessions."
    )
    parser.add_argument(
        "--session-id", type=str, help="Load a specific session ID to resume."
    )
    args = parser.parse_args()

    session_manager = SessionManager(observability_enabled=True)

    if args.list_sessions:
        sessions = session_manager.list_sessions()
        print(f"\n{COLOR_SYSTEM}=== Available Sessions ==={COLOR_RESET}")
        if not sessions:
            print("No sessions found.")
        for s in sessions:
            print(f"ID: {s['session_id']} | Last Updated: {s['last_updated']}")
        return

    print(f"\n{COLOR_SYSTEM}=== Personal AI Life Assistant ==={COLOR_RESET}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    score_data = load_score()

    # Auto-generate file if missing
    generate_daily_template(date_str, score_data)

    tools = [
        ReadFileTool(),
        WriteFileTool(),
        InsertFileTool(),
    ]

    agent = Agent(model_name=model_name, tools=tools)
    # base_url = "http://192.168.1.4:11434"

    if args.session_id:
        print(f"\n{COLOR_SYSTEM}[Loading Session: {args.session_id}...]{COLOR_RESET}")
        try:
            agent.messages = session_manager.load_session(args.session_id)
        except Exception as e:
            print(f"{COLOR_ERROR}Could not load session: {e}{COLOR_RESET}")
            return
    else:

        print(f"\n{COLOR_SYSTEM}[Initializing Context & Placeholders...]{COLOR_RESET}")
        prompt = build_system_prompt()
        # Override generic AgentShiro system prompt
        agent.messages = [{"role": "system", "content": prompt}]
        # Initialize a new session ID
        session_manager.create_session()

    print(
        f"\n{COLOR_SYSTEM}[Mode Activated. Score: {score_data['points']}, Level: {score_data['level']}, Streak: {score_data['streak']}]{COLOR_RESET}\n"
    )
    print(
        f"\n\033[1m{COLOR_USER}Chat started. Type 'exit' to quit.{COLOR_RESET}\033[0m\n"
    )

    while True:
        try:
            print(f"{COLOR_USER}User:{COLOR_RESET} ", end="", flush=True)
            user_input = input()
            if user_input.lower() in ["exit", "quit", ""]:
                break

            if user_input.startswith("/session"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1] == "list":
                    sessions = session_manager.list_sessions()
                    print(f"\n{COLOR_SYSTEM}=== Available Sessions ==={COLOR_RESET}")
                    for s in sessions:
                        print(
                            f"ID: {s['session_id']} | Last Updated: {s['last_updated']}"
                        )
                    print()
                    continue
                elif len(parts) > 2 and parts[1] == "load":
                    new_session_id = parts[2]
                    try:
                        agent.messages = session_manager.load_session(new_session_id)
                        print(
                            f"{COLOR_SYSTEM}Successfully loaded session {new_session_id}.{COLOR_RESET}\n"
                        )
                    except Exception as e:
                        print(f"Failed to load session: {e}\n")
                    continue
                else:
                    print("Usage: /session list OR /session load <id>\n")
                    continue

            run_agent_loop(agent, user_input)

            # Save session and observability after every turn
            session_manager.save_session(agent.messages)
            # session_manager.log_observability(agent.messages)

            print()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"\n\033[91mError: {str(e)}\033[0m\n")


if __name__ == "__main__":
    main()
