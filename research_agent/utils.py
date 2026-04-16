"""Utility functions for the Research Agent."""
import re
from typing import List, Tuple


def parse_planner_decision(text: str) -> Tuple[str, str]:
    """
    Parse planner response into action and query.

    Args:
        text: Planner response text

    Returns:
        Tuple of (action, query) where action is "Answer" or "Search"
    """
    if "Action: Answer" in text:
        return ("Answer", "")

    # Extract query from "Query: ..." pattern
    query_match = re.search(r"Query:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    query = query_match.group(1).strip() if query_match else "what is the answer"

    return ("Search", query)


def extract_queries(text: str) -> List[str]:
    """
    Extract numbered queries from text.

    Args:
        text: Text containing numbered queries

    Returns:
        List of query strings
    """
    queries = []
    lines = text.split("\n")

    for line in lines:
        # Match patterns like "1. query" or "1. query\n"
        match = re.match(r"^\d+\.\s*(.+?)(?:\n|$)", line)
        if match:
            queries.append(match.group(1).strip())

    return queries


def parse_facts(text: str) -> List[str]:
    """
    Extract facts from text (lines starting with '-').

    Args:
        text: Text containing facts as bullet points

    Returns:
        List of fact strings
    """
    facts = []
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-"):
            # Remove the dash and whitespace
            fact = stripped[1:].strip()
            if fact:
                facts.append(fact)

    return facts


def format_search_results(results) -> str:
    """
    Format search results for display in prompts.

    Args:
        results: List of SearchResult objects

    Returns:
        Formatted string
    """
    if not results:
        return "(no results)"

    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"{i}. Title: {result.title}\nSnippet: {result.snippet}")

    return "\n\n".join(formatted)


def format_facts(facts) -> str:
    """
    Format AtomicFact objects for display.

    Args:
        facts: List of AtomicFact objects

    Returns:
        Formatted string
    """
    if not facts:
        return "(no facts)"

    formatted = []
    for fact in facts:
        formatted.append(f"- {fact.fact}")

    return "\n".join(formatted)
