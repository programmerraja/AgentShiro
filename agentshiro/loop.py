import json
import uuid
import re
import ast
from litellm import stream_chunk_builder
from .llm import completion
from .agent import Agent

# ANSI Colors
COLOR_RESET = "\033[0m"
COLOR_AGENT = "\033[96m"  # Cyan
COLOR_TOOL_NAME = "\033[93m"  # Yellow
COLOR_TOOL_ARGS = "\033[95m"  # Magenta
COLOR_TOOL_RESULT = "\033[90m"  # Dark Gray
COLOR_ERROR = "\033[91m"  # Red


def run_agent_loop(agent: Agent, user_input: str, **kwargs) -> str:
    agent.add_user_message(user_input)
    # print(agent.model_name, "s")
    while True:
        tools = agent.get_provider_tools()

        response = completion(
            model=agent.model_name,
            messages=agent.messages,
            tools=tools,
            stream=True,
            **kwargs,
        )

        full_content = ""
        chunks = []

        print(f"{COLOR_AGENT}AgentShiro:{COLOR_RESET} ", end="", flush=True)

        for chunk in response:
            chunks.append(chunk)
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                print(content, end="", flush=True)
                full_content += content

        print()

        # We rely strictly on standard litellm chunk reconstruction.
        try:
            reconstructed = stream_chunk_builder(chunks, messages=agent.messages)
            response_message = reconstructed.choices[0].message
        except Exception as e:

            class DummyMessage:
                def __init__(self, content):
                    self.content = content
                    self.tool_calls = None

            response_message = DummyMessage(content=full_content)

        tool_calls = []
        if getattr(response_message, "tool_calls", None):
            for call in response_message.tool_calls:
                tool_calls.append(
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                )

        if tool_calls:
            message_dict = {
                "role": "assistant",
                "content": full_content,
                "tool_calls": tool_calls,
            }
            agent.add_message(message_dict)

            # Execute all tool calls
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]

                print(
                    f"\n  {COLOR_TOOL_NAME}⚡ Tool Execution: {function_name}{COLOR_RESET}"
                )
                print(f"  {COLOR_TOOL_ARGS}Arguments: {arguments_str}{COLOR_RESET}")

                tool = agent.get_tool(function_name)
                try:
                    arguments = json.loads(arguments_str) if arguments_str else {}
                    if tool:
                        result = tool.run(**arguments)
                    else:
                        result = f"Error: Tool {function_name} not found."
                except Exception as e:
                    result = f"Error executing tool {function_name}: {str(e)}"

                result_str = str(result)
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "\n...[truncated output]"

                indented_result = "\n".join(
                    "    " + line for line in result_str.split("\n")
                )
                print(f"  {COLOR_TOOL_RESULT}Result:\n{indented_result}{COLOR_RESET}\n")

                agent.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": str(result),
                    }
                )
        else:
            message_dict = {"role": "assistant", "content": full_content}
            agent.add_message(message_dict)
            return full_content
