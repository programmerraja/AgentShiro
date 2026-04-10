import subprocess
from pydantic import BaseModel, Field
from .base import BaseTool

class BashArgs(BaseModel):
    command: str = Field(..., description="The command string to execute in bash.")

class BashTool(BaseTool):
    name = "bash"
    description = "Execute a command in the bash shell. Use this to run system commands or inspect files."
    args_schema = BashArgs

    def run(self, command: str, **kwargs) -> str:
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output if output else "Command executed successfully with no output."
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"
