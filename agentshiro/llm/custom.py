import time
import uuid
import re
import ast
import json
from litellm.utils import ModelResponse, Message, Choices
from .base import BaseCustomLLM
from openai import OpenAI


def parse_inline_tools(content: str, available_tools: list = None):
    """
    Parses tools written inline in plain text, e.g., [bash(command="ls")]
    Returns a list of parsed tool calls securely.
    """
    pattern = r"\[([a-zA-Z0-9_\-]+)\((.*?)\)\]"
    matches = list(re.finditer(pattern, content, re.DOTALL))

    # Get a list of valid tool names to prevent hallucinated bracket formats from triggering tool calls
    valid_tool_names = None
    if available_tools:
        valid_tool_names = [t["function"]["name"] for t in available_tools]
    elif available_tools is not None and len(available_tools) == 0:
        return []

    tool_calls = []
    for match in matches:
        tool_name = match.group(1)
        args_str = match.group(2).strip()

        if valid_tool_names is not None and tool_name not in valid_tool_names:
            continue

        args_dict = {}
        if args_str:
            try:
                tree = ast.parse(f"dummy({args_str})")
                call = tree.body[0].value
                for kw in call.keywords:
                    try:
                        args_dict[kw.arg] = ast.literal_eval(kw.value)
                    except:
                        pass
            except Exception:
                args_dict["raw"] = args_str

        tool_calls.append(
            {
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {"name": tool_name, "arguments": json.dumps(args_dict)},
            }
        )
    return tool_calls


class ShiroCustomProvider(BaseCustomLLM):
    """
    A Custom LLM Provider that connects to an API seamlessly,
    proxying streaming natively by converting OpenAI chunks to LiteLLM's internal generic chunk format.
    """

    def __init__(self):
        super().__init__()

    def completion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        base_url = kwargs.get("api_base", "http://192.168.1.4:8080")

        tools = kwargs.get("optional_params", {}).get("tools")
        api_kwargs = {"model": model, "messages": messages}
        if tools:
            api_kwargs["tools"] = tools

        client = OpenAI(api_key="dummy", base_url="http://192.168.1.4:8080")
        completion_resp = client.chat.completions.create(**api_kwargs)
        content = completion_resp.choices[0].message.content or ""

        tool_calls = parse_inline_tools(content, available_tools=tools)

        message_kwargs = {"content": content, "role": "assistant"}
        if tool_calls:
            message_kwargs["tool_calls"] = tool_calls

        message = Message(**message_kwargs)

        choice = Choices(
            index=0,
            message=message,
            finish_reason="tool_calls" if tool_calls else "stop",
        )

        return ModelResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            choices=[choice],
            created=int(time.time()),
            model=model,
            object="chat.completion",
        )

    def streaming(self, model: str, messages: list, **kwargs):
        base_url = kwargs.get("api_base", "http://localhost:8080")
        tools = kwargs.get("optional_params", {}).get("tools")
        api_kwargs = {"model": model, "messages": messages}
        if tools:
            api_kwargs["tools"] = tools

        client = OpenAI(api_key="dummy", base_url="http://192.168.1.4:1234")

        completion_resp = client.chat.completions.create(**api_kwargs, stream=True)

        def stream_generator():
            content_buffer = ""
            for chunk in completion_resp:
                if chunk.choices and getattr(chunk.choices[0].delta, "content", None):
                    text = chunk.choices[0].delta.content
                    content_buffer += text
                    yield {
                        "text": text,
                        "is_finished": False,
                        "finish_reason": "",
                        "usage": None,
                    }

            tool_calls = parse_inline_tools(content_buffer, available_tools=tools)

            if tool_calls:
                for idx, tc in enumerate(tool_calls):
                    yield {
                        "text": "",
                        "is_finished": False,
                        "finish_reason": "",
                        "usage": None,
                        "tool_use": {
                            "index": idx,
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        },
                    }
                yield {
                    "text": "",
                    "is_finished": True,
                    "finish_reason": "tool_calls",
                    "usage": None,
                }
            else:
                yield {
                    "text": "",
                    "is_finished": True,
                    "finish_reason": "stop",
                    "usage": None,
                }

        return stream_generator()
