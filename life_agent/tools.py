import os
from pydantic import BaseModel, Field
from agentshiro.tools.base import BaseTool

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "life-system")
)


def _resolve_path(path_str):
    if not path_str.startswith("life-system/"):
        path_str = f"life-system/{path_str.lstrip('/')}"
    rel_path = path_str.replace("life-system/", "", 1)
    target = os.path.abspath(os.path.join(BASE_DIR, rel_path))
    if not target.startswith(BASE_DIR):
        raise ValueError("Cannot access paths outside life-system directory.")
    return target


class ReadFileSchema(BaseModel):
    path: str = Field(
        ...,
        description="Path to the file, e.g., 'life-system/daily/2026/04/2026-04-10.md'",
    )


class ReadFileTool(BaseTool):
    name = "readFile"
    description = "Reads a file and returns its content with line numbers prefixed."
    args_schema = ReadFileSchema

    def run(self, path: str, **kwargs) -> str:
        try:
            target = _resolve_path(path)
            if not os.path.exists(target):
                return f"Error: File {path} not found."
            with open(target, "r") as f:
                lines = f.readlines()
            numbered = [f"{i+1}: {line}" for i, line in enumerate(lines)]
            return "".join(numbered)
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileSchema(BaseModel):
    path: str = Field(
        ..., description="Path to the file, e.g., 'life-system/mistakes/2026-04-10.md'"
    )
    content: str = Field(..., description="The entire content to write to the file.")


class WriteFileTool(BaseTool):
    name = "writeFile"
    description = "Writes completely new content to a file, overwriting if it exists."
    args_schema = WriteFileSchema

    def run(self, path: str, content: str, **kwargs) -> str:
        try:
            target = _resolve_path(path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class InsertFileSchema(BaseModel):
    path: str = Field(..., description="Path to the file.")
    content: str = Field(..., description="Content to insert. Can be multiple lines.")
    lineNo: int = Field(
        ..., description="Line number (1-indexed) to insert the content BEFORE."
    )


class InsertFileTool(BaseTool):
    name = "insertFile"
    description = "Inserts content at the specified line number, shifting the existing lines down."
    args_schema = InsertFileSchema

    def run(self, path: str, content: str, lineNo: int, **kwargs) -> str:
        try:
            target = _resolve_path(path)
            if not os.path.exists(target):
                return f"Error: File {path} not found."
            with open(target, "r") as f:
                lines = f.readlines()

            idx = max(0, min(lineNo - 1, len(lines)))
            if not content.endswith("\n"):
                content += "\n"

            lines.insert(idx, content)

            with open(target, "w") as f:
                f.writelines(lines)
            return f"Successfully inserted content at line {lineNo} in {path}"
        except Exception as e:
            return f"Error inserting into file: {str(e)}"
