"""
Core data types for the Research Agent.
"""
from dataclasses import dataclass, field
from typing import List
import json


@dataclass
class SearchResult:
    """Represents a search result from a search provider."""
    title: str
    url: str
    snippet: str


@dataclass
class LLMResponse:
    """Represents a response from an LLM provider."""
    text: str
    cost: float = 0.0
    reasoning: str = ""


@dataclass
class Result:
    """Final result from the research agent."""
    answer: str
    cost: float = 0.0
    knowledge: str = ""


@dataclass
class Scratchpad:
    """State management for the scratchpad strategy."""
    original_question: str
    current_step: str = ""
    knowledge: str = ""
    history: List[str] = field(default_factory=list)
    iteration_count: int = 0

    def snapshot(self) -> str:
        """Return a text snapshot of the current state."""
        return f"""Question:
{self.original_question}

Current Step:
{self.current_step or "(none yet)"}

Knowledge:
{self.knowledge.strip() if self.knowledge else "(empty)"}

History:
{chr(10).join(self.history) if self.history else "(none)"}

Iteration: {self.iteration_count}"""

    def append_history(self, entry: str):
        """Add an entry to the history."""
        if entry:
            self.history.append(entry)


@dataclass
class AtomicFact:
    """Represents an atomic fact extracted from search results."""
    fact: str
    source: str


@dataclass
class Notebook:
    """Accumulates atomic facts from multiple searches."""
    facts: List[AtomicFact] = field(default_factory=list)

    def add_fact(self, fact: str, source: str):
        """Add a fact with deduplication."""
        new_fact = AtomicFact(fact=fact, source=source)

        # Check for duplicates or substrings
        is_duplicate = any(
            f.fact == fact or fact in f.fact or f.fact in fact
            for f in self.facts
        )

        if not is_duplicate:
            self.facts.append(new_fact)

    def to_json(self) -> str:
        """Serialize notebook to JSON."""
        return json.dumps(
            [{"fact": f.fact, "source": f.source} for f in self.facts],
            indent=2
        )

    @staticmethod
    def from_json(json_str: str) -> "Notebook":
        """Deserialize notebook from JSON."""
        notebook = Notebook()
        try:
            data = json.loads(json_str)
            for item in data:
                notebook.facts.append(
                    AtomicFact(fact=item["fact"], source=item["source"])
                )
        except (json.JSONDecodeError, KeyError):
            pass
        return notebook
