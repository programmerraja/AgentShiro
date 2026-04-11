import os
import sys
from dotenv import load_dotenv

load_dotenv()

from agentshiro.agent import Agent
from agentshiro.loop import run_agent_loop
from agentshiro.tools.bash import BashTool

COLOR_USER = "\033[92m"  # Green
COLOR_RESET = "\033[0m"

model_name = "LFM2.5-1.2B-Thinking-GGUF:BF16"
# "LiquidAI/LFM2.5-1.2B-Instruct-GGUF"


def main():
    tools = [BashTool()]

    agent = Agent(model_name=model_name, tools=tools)

    print(
        f"\n\033[1m{COLOR_USER}Welcome to AgentShiro. Type 'exit' to quit.{COLOR_RESET}\033[0m\n"
    )

    while True:
        try:
            print(f"{COLOR_USER}User:{COLOR_RESET} ", end="", flush=True)
            user_input = input()
            if user_input.lower() in ["exit", "quit", ""]:
                break

            run_agent_loop(agent, user_input)
            print()  # visual padding between turns

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n\033[91mError: {str(e)}\033[0m\n")


if __name__ == "__main__":
    main()
