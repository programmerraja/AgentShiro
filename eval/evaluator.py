"""
Life-Assistant Test Evaluator
Evaluates the life-assistant agent against test cases using LLM-as-user and LLM-as-judge.
"""

import json
import logging
import os
import re
import shutil
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from agentshiro.agent import Agent
from life_agent.prompt_builder import build_system_prompt
from agentshiro.loop import run_agent_loop
from agentshiro.llm import completion
from agentshiro.tools.base import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

EVAL_MODEL = "nvidia_nim/qwen/qwen3-next-80b-a3b-instruct"
USER_MODEL = "nvidia_nim/qwen/qwen3-next-80b-a3b-instruct"
AGENT_MODEL = "nvidia_nim/qwen/qwen3-next-80b-a3b-instruct"


def _resolve_path(base_dir: str, path: str) -> str:
    """Resolve and validate a file path within base_dir with security checks."""
    if not path.startswith("life-system/"):
        path = f"life-system/{path.lstrip('/')}"
    rel_path = path.replace("life-system/", "", 1)
    target = os.path.abspath(os.path.join(base_dir, rel_path))

    if not target.startswith(base_dir):
        raise ValueError("Cannot access paths outside life-system directory.")

    return target


class TestReadFileSchema(BaseModel):
    path: str = Field(
        ...,
        description="Path to the file, e.g., 'life-system/daily/2026/04/2026-04-10.md'",
    )


class TestReadFileTool(BaseTool):
    """ReadFile tool that uses a custom base directory"""

    name = "readFile"
    description = "Reads a file and returns its content with line numbers prefixed."
    args_schema = TestReadFileSchema
    base_dir: str = ""

    def run(self, path: str, **kwargs) -> str:
        try:
            target = _resolve_path(self.base_dir, path)

            if not os.path.exists(target):
                return f"Error: File {path} not found."

            with open(target, "r") as f:
                lines = f.readlines()
            numbered = [f"{i+1}: {line}" for i, line in enumerate(lines)]
            return "".join(numbered)
        except Exception as e:
            return f"Error reading file: {str(e)}"


class TestWriteFileSchema(BaseModel):
    path: str = Field(
        ..., description="Path to the file, e.g., 'life-system/mistakes/2026-04-10.md'"
    )
    content: str = Field(..., description="The entire content to write to the file.")


class TestWriteFileTool(BaseTool):
    """WriteFile tool that uses a custom base directory"""

    name = "writeFile"
    description = "Writes completely new content to a file, overwriting if it exists."
    args_schema = TestWriteFileSchema
    base_dir: str = ""

    def run(self, path: str, content: str, **kwargs) -> str:
        try:
            target = _resolve_path(self.base_dir, path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class TestInsertFileSchema(BaseModel):
    path: str = Field(..., description="Path to the file.")
    content: str = Field(..., description="Content to insert. Can be multiple lines.")
    lineNo: int = Field(
        ..., description="Line number (1-indexed) to insert the content BEFORE."
    )


class TestInsertFileTool(BaseTool):
    """InsertFile tool that uses a custom base directory"""

    name = "insertFile"
    description = "Inserts content at the specified line number, shifting the existing lines down."
    args_schema = TestInsertFileSchema
    base_dir: str = ""

    def run(self, path: str, content: str, lineNo: int, **kwargs) -> str:
        try:
            target = _resolve_path(self.base_dir, path)

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


class JudgeScore(BaseModel):
    """Scores from LLM judge"""

    tool_accuracy: float
    alignment_detection: float
    planning_quality: float
    reflection_quality: float
    weighted_score: float
    reasoning: Dict[str, str]
    pass_fail: bool
    eval_prompt: Optional[str] = None
    raw_response: Optional[str] = None


class TestResult(BaseModel):
    """Result of a single test"""

    test_id: str
    title: str
    status: str  # "passed", "failed", "error"
    messages: Optional[List[Dict[str, Any]]] = None
    judge_score: Optional[JudgeScore] = None
    error_message: Optional[str] = None
    files_changed: Dict[str, Dict[str, Any]] = {}
    duration_seconds: float = 0.0


class StateManager:
    """Manages test state setup and cleanup"""

    def __init__(self, template_dir: str, test_runs_dir: str):
        self.template_dir = template_dir
        self.test_runs_dir = test_runs_dir
        Path(test_runs_dir).mkdir(parents=True, exist_ok=True)

    def setup_test_state(self, test_id: str, initial_state: Dict[str, Any]) -> str:
        """
        Setup a test's life-system copy with initial state.
        Returns the path to the test's life-system directory.
        """
        test_dir = Path(self.test_runs_dir) / f"test_{test_id}"
        life_system_path = test_dir / "life-system"

        # Create test directory
        test_dir.mkdir(parents=True, exist_ok=True)

        # Copy template
        if life_system_path.exists():
            shutil.rmtree(life_system_path)
        shutil.copytree(self.template_dir, life_system_path)

        # Create initial state files
        files_to_create = initial_state.get("files_to_create", {})
        for file_path, content in files_to_create.items():
            full_path = life_system_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(content, dict):
                # Write JSON
                with open(full_path, "w") as f:
                    json.dump(content, f, indent=2)
            else:
                # Write text
                with open(full_path, "w") as f:
                    f.write(content)

        return str(life_system_path)

    def get_test_dir(self, test_id: str) -> str:
        """Get the test directory path"""
        return str(Path(self.test_runs_dir) / f"test_{test_id}")

    def cleanup_test(self, test_id: str, keep_files: bool = True):
        """Cleanup test directory (optionally keeping files for inspection)"""
        if not keep_files:
            test_dir = self.get_test_dir(test_id)
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)


class UserAgent:
    """LLM-based user agent that follows instructions from test case prompt"""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.model = USER_MODEL
        self.agent = Agent(model_name=self.model, tools=[])
        self.agent.messages = [{"role": "system", "content": system_prompt}]
        self.end_called = False

    def add_assistant_message(self, message: str):
        """Add assistant's response to history (what user sees)"""
        self.agent.add_message({"role": "assistant", "content": message})

    def get_next_message(self) -> Optional[str]:
        """Get next user message using agentshiro"""
        try:
            message_text = run_agent_loop(self.agent, "")

            # Check if user called end tool (indicated by [END] in response)
            if "[END]" in message_text:
                self.end_called = True
                # Still add to history so judge can see it
                self.agent.add_message({"role": "user", "content": message_text})
                return None

            self.agent.add_message({"role": "user", "content": message_text})

            return message_text

        except Exception as e:
            logger.error(f"Error getting user message: {e}")
            return None


class ConversationRunner:
    """Runs a conversation between user and assistant"""

    def __init__(self, test_case: Dict[str, Any], life_system_path: str):
        self.test_case = test_case
        self.life_system_path = life_system_path
        self.start_time = None
        self.end_time = None

    def run(self) -> List[Dict[str, Any]]:
        """Run the conversation loop"""
        self.start_time = time.time()
        safeguards = self.test_case.get("safeguards", {})
        max_turns = safeguards.get("max_turns", 15)
        # timeout_seconds = safeguards.get("timeout_seconds", 300)

        user_prompt = self.test_case["user_agent_prompt"]
        user_agent = UserAgent(system_prompt=user_prompt)

        read_tool = TestReadFileTool()
        read_tool.base_dir = self.life_system_path
        write_tool = TestWriteFileTool()
        write_tool.base_dir = self.life_system_path
        insert_tool = TestInsertFileTool()
        insert_tool.base_dir = self.life_system_path

        tools = [read_tool, write_tool, insert_tool]

        life_assistant = Agent(model_name=AGENT_MODEL, tools=tools)

        system_prompt = build_system_prompt()
        life_assistant.messages = [{"role": "system", "content": system_prompt}]

        turn_number = 1

        # Get first user message
        first_message = user_agent.get_next_message()
        if not first_message:
            self.end_time = time.time()
            return self._get_conversation_messages(life_assistant)

        while turn_number <= max_turns:
            # elapsed = time.time() - self.start_time
            # if elapsed > timeout_seconds:
            #     print(f"  ⏱️  Timeout reached ({timeout_seconds}s)")
            #     break

            logger.info(f"Turn {turn_number}: User: {first_message[:80]}...")

            assistant_response = run_agent_loop(life_assistant, first_message)

            logger.info(f"Assistant: {assistant_response[:80]}...")

            user_agent.add_assistant_message(assistant_response)

            if user_agent.end_called:
                logger.info("User called end tool")
                self.end_time = time.time()
                return self._get_conversation_messages(life_assistant)

            first_message = user_agent.get_next_message()
            if first_message is None:
                self.end_time = time.time()
                return self._get_conversation_messages(life_assistant)

            turn_number += 1

        self.end_time = time.time()
        return self._get_conversation_messages(life_assistant)

    def _get_conversation_messages(self, life_assistant: Agent) -> List[Dict[str, Any]]:
        """Extract conversation messages (skip system message)"""
        return life_assistant.messages[1:]


class JudgeLLM:
    """LLM-based judge that evaluates conversation using LAB dimensions"""

    def __init__(self):
        self.model = EVAL_MODEL

    def evaluate(
        self, test_case: Dict[str, Any], messages: List[Dict[str, Any]]
    ) -> JudgeScore:
        """Evaluate conversation across LAB dimensions"""

        eval_prompt = self._build_eval_prompt(test_case, messages)

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": eval_prompt}],
                tools=None,
                stream=False,
            )

            response_text = response.choices[0].message.content
            logger.debug(f"Judge raw response: {response_text}")
            scores = self._parse_scores(response_text, test_case)
            scores.eval_prompt = eval_prompt
            scores.raw_response = response_text

            return scores

        except Exception as e:
            logger.error(f"Error in judge evaluation: {e}")
            return JudgeScore(
                tool_accuracy=0.0,
                alignment_detection=0.0,
                planning_quality=0.0,
                reflection_quality=0.0,
                weighted_score=0.0,
                reasoning={"error": str(e)},
                pass_fail=False,
                eval_prompt=eval_prompt,
                raw_response=None,
            )

    def _build_eval_prompt(
        self, test_case: Dict[str, Any], messages: List[Dict[str, Any]]
    ) -> str:
        """Build the evaluation prompt"""

        conv_text = self._format_messages_for_eval(messages)

        prompt = f"""
You are evaluating a Life-Assistant agent using the LAB (Life-Assistant Benchmark) framework.

## Test Case
ID: {test_case['test_id']}
Title: {test_case['title']}
Ground Truth Requirements:
{json.dumps(test_case['ground_truth'], indent=2)}

## Conversation
{conv_text}

## Evaluation Task
Score the agent on 4 dimensions (0-1 scale):

1. **Tool Accuracy** (0-1): Did the agent use the right tools with right arguments?
   - Read correct files? Wrote to correct locations?
   - Arguments match expected format?

2. **Alignment Detection** (0-1): Did agent understand user context and goals?
   - Correctly identified conflicts?
   - Detected alignment/misalignment accurately?

3. **Planning Quality** (0-1): Were suggestions realistic, actionable, distributed?
   - Fits time constraints?
   - Respects user context (work hours, goals)?
   - Provides specific times/durations?

4. **Reflection Quality** (0-1): Were insights meaningful, specific, goal-aligned?
   - Identifies real patterns (not hallucinated)?
   - Connects to stated goals?
   - Suggests concrete next steps?

## Your Response
Format your response EXACTLY as JSON (no markdown, no explanation):
{{
    "tool_accuracy": <float 0-1>,
    "alignment_detection": <float 0-1>,
    "planning_quality": <float 0-1>,
    "reflection_quality": <float 0-1>,
    "tool_accuracy_reasoning": "<short explanation>",
    "alignment_reasoning": "<short explanation>",
    "planning_reasoning": "<short explanation>",
    "reflection_reasoning": "<short explanation>",
    "pass": <true or false>
}}
"""
        return prompt

    def _format_messages_for_eval(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into readable conversation text"""
        conv_text = []
        turn_num = 1

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                conv_text.append(f"Turn {turn_num}:\n  User: {content}")
            elif role == "assistant":
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tools_str = ", ".join([tc["function"]["name"] for tc in tool_calls])
                    conv_text.append(
                        f"  Assistant: {content}\n  [Called tools: {tools_str}]"
                    )
                else:
                    conv_text.append(f"  Assistant: {content}")
                turn_num += 1
            elif role == "tool":
                tool_result = content[:200] + "..." if len(content) > 200 else content
                conv_text.append(
                    f"  [Tool result from {msg.get('name', 'unknown')}: {tool_result}]"
                )

        return "\n".join(conv_text)

    def _parse_scores(
        self, response_text: str, test_case: Dict[str, Any]
    ) -> JudgeScore:
        """Parse scores from judge response"""

        try:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            json_str = json_match.group(0)
            data = json.loads(json_str)

            weighted = (
                data.get("tool_accuracy", 0) * 0.25
                + data.get("alignment_detection", 0) * 0.25
                + data.get("planning_quality", 0) * 0.25
                + data.get("reflection_quality", 0) * 0.25
            )

            return JudgeScore(
                tool_accuracy=data.get("tool_accuracy", 0),
                alignment_detection=data.get("alignment_detection", 0),
                planning_quality=data.get("planning_quality", 0),
                reflection_quality=data.get("reflection_quality", 0),
                weighted_score=weighted,
                reasoning={
                    "tool_accuracy": data.get("tool_accuracy_reasoning", ""),
                    "alignment_detection": data.get("alignment_reasoning", ""),
                    "planning_quality": data.get("planning_reasoning", ""),
                    "reflection_quality": data.get("reflection_reasoning", ""),
                },
                pass_fail=data.get("pass", weighted > 0.6),
            )
        except Exception as e:
            logger.error(f"Error parsing judge scores: {e}")
            return JudgeScore(
                tool_accuracy=0.0,
                alignment_detection=0.0,
                planning_quality=0.0,
                reflection_quality=0.0,
                weighted_score=0.0,
                reasoning={"error": str(e)},
                pass_fail=False,
            )


class ResultsCollector:
    """Collects and saves test results"""

    def __init__(self, test_dir: str):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def _write_json(self, filename: str, data: dict):
        """Write JSON data to a file"""
        with open(self.test_dir / filename, "w") as f:
            json.dump(data, f, indent=2)

    def _write_text(self, filename: str, content: str):
        """Write text content to a file"""
        with open(self.test_dir / filename, "w") as f:
            f.write(content)

    def save_result(self, result: TestResult):
        """Save test result to files"""

        # Save messages
        if result.messages:
            self._write_json("messages.json", result.messages)

        if result.judge_score:
            score_data = {
                "tool_accuracy": result.judge_score.tool_accuracy,
                "alignment_detection": result.judge_score.alignment_detection,
                "planning_quality": result.judge_score.planning_quality,
                "reflection_quality": result.judge_score.reflection_quality,
                "weighted_score": result.judge_score.weighted_score,
                "pass": result.judge_score.pass_fail,
                "reasoning": result.judge_score.reasoning,
            }
            self._write_json("judge_scores.json", score_data)

            if result.judge_score.eval_prompt:
                self._write_text("eval_prompt.txt", result.judge_score.eval_prompt)

            if result.judge_score.raw_response:
                self._write_text("judge_response.txt", result.judge_score.raw_response)

        result_data = {
            "test_id": result.test_id,
            "title": result.title,
            "status": result.status,
            "error_message": result.error_message,
            "duration_seconds": result.duration_seconds,
        }
        self._write_json("result.json", result_data)


class TestRunner:

    def __init__(self, test_cases_file: str, template_dir: str, test_runs_dir: str):
        self.test_cases_file = test_cases_file
        self.state_manager = StateManager(template_dir, test_runs_dir)
        self.judge = JudgeLLM()
        self.results = []
        self._default_assistant_prompt = ""

    def run_all(self):
        with open(self.test_cases_file, "r") as f:
            data = json.load(f)

        test_cases = data.get("test_cases", [])
        self._default_assistant_prompt = data.get("default_assistant_prompt", "")

        logger.info(
            f"Life-Assistant Test Evaluator - Running {len(test_cases)} test cases"
        )

        for test_case in test_cases:
            logger.info(f"Running: {test_case['test_id']} - {test_case['title']}")
            result = self._run_single_test(test_case)
            self.results.append(result)

            if result.judge_score:
                status_emoji = "✅" if result.judge_score.pass_fail else "❌"
                logger.info(
                    f"  {status_emoji} Score: {result.judge_score.weighted_score:.2f}"
                )
            else:
                logger.error(f"  Error: {result.error_message}")

        self._generate_report()

    def _run_single_test(self, test_case: Dict[str, Any]) -> TestResult:
        """Run a single test case"""
        test_id = test_case["test_id"]

        try:
            life_system_path = self.state_manager.setup_test_state(
                test_id, test_case.get("initial_state", {})
            )

            test_dir = self.state_manager.get_test_dir(test_id)

            runner = ConversationRunner(test_case, life_system_path)
            messages = runner.run()

            judge_score = self.judge.evaluate(test_case, messages)

            collector = ResultsCollector(test_dir)

            duration = runner.end_time - runner.start_time if runner.end_time else 0

            result = TestResult(
                test_id=test_id,
                title=test_case["title"],
                status="passed" if judge_score.pass_fail else "failed",
                messages=messages,
                judge_score=judge_score,
                error_message=None,
                files_changed={},
                duration_seconds=duration,
            )

            collector.save_result(result)
            return result

        except Exception as e:
            logger.exception(f"Exception running test: {str(e)}")

            return TestResult(
                test_id=test_id,
                title=test_case.get("title", "Unknown"),
                status="error",
                messages=None,
                judge_score=None,
                error_message=str(e),
                files_changed={},
                duration_seconds=0,
            )

    def _generate_report(self):
        """Generate final report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.status == "passed"),
            "failed": sum(1 for r in self.results if r.status == "failed"),
            "errors": sum(1 for r in self.results if r.status == "error"),
            "average_score": sum(
                r.judge_score.weighted_score for r in self.results if r.judge_score
            )
            / max(1, sum(1 for r in self.results if r.judge_score)),
            "results": [
                {
                    "test_id": r.test_id,
                    "title": r.title,
                    "status": r.status,
                    "weighted_score": (
                        r.judge_score.weighted_score if r.judge_score else None
                    ),
                    "duration_seconds": r.duration_seconds,
                }
                for r in self.results
            ],
        }

        logger.info(
            f"Test Summary Report: {report['total_tests']} total, {report['passed']} passed, {report['failed']} failed, {report['errors']} errors, {report['average_score']:.2f} avg score"
        )

        report_file = (
            Path(self.test_cases_file).parent.parent
            / "test_runs"
            / "summary_report.json"
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to: {report_file}")


if __name__ == "__main__":

    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_file = os.path.join(current_dir, "test_cases.json")
    template_dir = os.path.join(current_dir, "template_life_system")
    test_runs_dir = os.path.join(current_dir, "test_runs")

    runner = TestRunner(test_cases_file, template_dir, test_runs_dir)
    runner.run_all()
