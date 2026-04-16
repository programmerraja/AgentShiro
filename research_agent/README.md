# Research Agent

An AI-powered research agent that answers questions through iterative search, fact extraction, and synthesis. Built on top of AgentShiro's framework.

## Features

- **Two Research Strategies**:
  - **Scratchpad**: Simple iterative approach (planner → search → synthesize)
  - **Graph Reader**: Complex research with atomic fact extraction and adaptive queries

- **Pluggable Providers**:
  - **LLM**: Support for any litellm-compatible model (Claude, GPT-4, Ollama, etc.)
  - **Search**: DuckDuckGo (free), Mock for testing
  - **Fetch**: HTTP with HTML stripping for deep reading

- **Cost Tracking**: Automatic token counting and cost calculation

- **Fact Deduplication**: Intelligent notebook system prevents duplicate facts

## Installation

```bash
# Install dependencies
pip install aiohttp litellm

# Run examples
python research-agent/example.py
```

## Quick Start

### Basic Usage

```python
import asyncio
from research_agent import ResearchAgent

async def main():
    agent = ResearchAgent(
        model_name="nvidia_nim/qwen/qwen3-next-80b-a3b-instruct",
        strategy="scratchpad",
        max_iterations=5
    )
    
    result = await agent.answer("Who won the 2024 Nobel Prize in Chemistry?")
    
    print(f"Answer: {result.answer}")
    print(f"Cost: ${result.cost:.4f}")

asyncio.run(main())
```

### Using Different Strategies

```python
# Scratchpad (default) - faster, simpler
agent = ResearchAgent(strategy="scratchpad")

# Graph Reader - more thorough research
agent = ResearchAgent(strategy="graph-reader")
```

### Custom Providers

```python
from research_agent import (
    ResearchAgent,
    MockLLM,
    MockSearch,
    SearchResult
)

# Mock for testing (no API calls)
agent = ResearchAgent(
    llm_provider=MockLLM(),
    search_provider=MockSearch([
        SearchResult("Title", "https://example.com", "Snippet")
    ])
)
```

## Architecture

```
research-agent/
├── agent.py                 # Main ResearchAgent class
├── types.py                 # Data classes (SearchResult, Result, etc)
├── prompts.py               # System prompts for strategies
├── utils.py                 # Parsing utilities
├── providers/               # Abstract provider interfaces
│   ├── llm_provider.py
│   ├── search_provider.py
│   └── fetch_provider.py
├── implementations/         # Concrete provider implementations
│   ├── llm/                 # LiteLLMProvider, MockLLM
│   ├── search/              # DuckDuckGoSearch, MockSearch
│   └── fetch/               # HTTPFetch, MockFetch
└── strategies/              # Research algorithms
    ├── base_strategy.py
    ├── scratchpad_strategy.py
    └── graph_reader_strategy.py
```

## Strategies

### Scratchpad Strategy

**Best for**: Quick questions, fact-checking

```
Question: "Why is the sky blue?"
    ↓
Iteration 1: Planner → "Search for: why is sky blue"
Iteration 1: Search → DuckDuckGo finds 5 results
Iteration 1: Synthesize → "Rayleigh scattering causes..."
    ↓
Iteration 2: Planner → "Action: Answer" (enough info)
    ↓
Finalizer → "The sky appears blue due to Rayleigh scattering..."
    ↓
Result: answer, cost, knowledge
```

### Graph Reader Strategy

**Best for**: Complex research, multi-faceted questions

```
Question: "Benefits of renewable energy and leading countries?"
    ↓
Plan: Break into 3-5 key queries
Queue: ["renewable benefits", "solar adoption", "wind leaders", ...]
    ↓
For each query (up to 8 steps):
  - Search
  - Extract atomic facts → Notebook
  - If 5+ facts: done
  - Else: generate neighbor queries
    ↓
Finalizer → Comprehensive answer from facts
    ↓
Result: answer, cost, facts as JSON
```

## Data Types

### Result
```python
@dataclass
class Result:
    answer: str          # Final answer
    cost: float          # Total LLM + search cost
    knowledge: str       # Collected knowledge (text or JSON)
```

### SearchResult
```python
@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
```

### Notebook (Graph Reader)
```python
notebook = Notebook()
notebook.add_fact("David Baker won Nobel Prize 2024", "source_url")
notebook.to_json()  # Serialize for reuse
```

## Examples

See `example.py` for:
- Mock testing (no API calls)
- Real LLM + DuckDuckGo
- Graph Reader strategy
- Follow-up questions with knowledge reuse

## Configuration

### LLM Models

Any litellm-supported model:
```python
# Claude
ResearchAgent(model_name="claude-3-5-sonnet-20241022")

# GPT-4
ResearchAgent(model_name="gpt-4-turbo")

# Ollama (local)
ResearchAgent(model_name="ollama/mistral")
```

### Max Iterations

```python
agent = ResearchAgent(max_iterations=5)  # Default
agent = ResearchAgent(max_iterations=10)  # Deeper research
```

## Cost Tracking

The agent tracks costs automatically:
```python
result = await agent.answer("question")
print(f"Cost: ${result.cost:.4f}")  # Total LLM call costs
```

**Note**: Search is currently free (DuckDuckGo). Costs are primarily from LLM tokens.

## Testing

```python
from research_agent import ResearchAgent, MockLLM, MockSearch, SearchResult

mock_results = [
    SearchResult("Title", "https://example.com", "Snippet...")
]

agent = ResearchAgent(
    llm_provider=MockLLM(),
    search_provider=MockSearch(mock_results)
)

result = await agent.answer("test question")
```

## Extending

### Custom LLM Provider

```python
from research_agent.providers import LLMProvider
from research_agent.types import LLMResponse

class MyLLM(LLMProvider):
    async def generate(self, system_prompt, user_prompt):
        # Your implementation
        return LLMResponse(text="answer", cost=0.01)
```

### Custom Search Provider

```python
from research_agent.providers import SearchProvider
from research_agent.types import SearchResult

class MySearch(SearchProvider):
    async def search(self, query):
        # Your implementation
        return [SearchResult(...)]
```

## Limitations

- Async-only (no sync API yet)
- DuckDuckGo search may rate-limit on heavy use
- Cost calculation is approximate (depends on litellm)
- No web scraping depth (HTTPFetch for snippets only)

## Future Enhancements

- [ ] Brave Search integration
- [ ] Web scraping depth
- [ ] Fact verification
- [ ] Citation tracking
- [ ] Streaming responses
- [ ] Multi-turn conversations
