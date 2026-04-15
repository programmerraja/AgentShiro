from datetime import datetime
from typing import List, Dict, Any

from agentshiro.session import SessionManager
from .tools.base import BaseTool
from .prompts import SYSTEM_PROMPT_TEMPLATE


class Agent:
    def __init__(self, model_name: str, tools: List[BaseTool] = None):
        self.model_name = model_name
        self.tools = tools or []
        self.messages: List[Dict[str, Any]] = []
        self.session_manager = SessionManager(observability_enabled=True)
        self._init_system_prompt()

    def _init_system_prompt(self):
        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.messages.append({"role": "system", "content": system_content})

    def get_tool(self, name: str) -> BaseTool | None:
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def get_provider_tools(self) -> List[dict] | None:
        if not self.tools:
            return None
        return [tool.to_openai_tool() for tool in self.tools]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_message(self, message: dict):
        self.messages.append(message)
        self.session_manager.save_session(self.messages)
