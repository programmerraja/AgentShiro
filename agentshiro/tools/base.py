from typing import Any, Type
from pydantic import BaseModel

class BaseTool:
    name: str = "base_tool"
    description: str = "A tool."
    args_schema: type[BaseModel] | None = None

    def run(self, **kwargs) -> Any:
        raise NotImplementedError

    def to_openai_tool(self) -> dict:
        tool_dict = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            }
        }
        if self.args_schema:
            tool_dict["function"]["parameters"] = self.args_schema.model_json_schema()
        else:
            tool_dict["function"]["parameters"] = {
                "type": "object",
                "properties": {},
                "required": []
            }
        return tool_dict
