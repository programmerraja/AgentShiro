from pydantic import BaseModel, Field
from .base import BaseTool

class CalculatorArgs(BaseModel):
    expression: str = Field(..., description="A mathematical expression to evaluate, e.g., '2 + 2 * 3'.")

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a mathematical expression."
    args_schema = CalculatorArgs

    def run(self, expression: str, **kwargs) -> str:
        try:
            # Note: eval is generally discouraged but works for simple math here.
            # Using __builtins__: None limits the scope of execution.
            result = eval(expression, {"__builtins__": None}, {})
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
