# Research Agent Implementation Plan (Python)

## Overview
Implement a research agent in Python using the AgentShiro base framework, adapting the Node.js research agent design to leverage AgentShiro's architecture (agent loop, tools, sessions, litellm integration).

---

## Architecture Decision

### Core Design
- **Extend AgentShiro's Agent class** to inherit session management, tool execution, and streaming
- **Plugin-based providers** for LLM, Search, Fetch (abstract classes with concrete implementations)
- **Two strategies** (Scratchpad and GraphReader) as pluggable strategy classes
- **Use litellm** for all LLM calls (already integrated in AgentShiro)
- **Reuse existing tools system** where applicable

### Directory Structure
```
research-agent/
├── __init__.py
├── agent.py                    # ResearchAgent extending agentshiro.Agent
├── types.py                    # Data classes: SearchResult, LLMResponse, Result, Scratchpad, AtomicFact, Notebook
├── prompts.py                  # System prompts for planner, synthesizer, extractor, finalizer, neighbor
├── providers/
│   ├── __init__.py
│   ├── llm_provider.py         # Abstract LLMProvider (abstract class)
│   ├── search_provider.py      # Abstract SearchProvider (abstract class)
│   └── fetch_provider.py       # Abstract FetchProvider (abstract class)
├── implementations/
│   ├── __init__.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── duckduckgo.py       # DuckDuckGoSearch
│   ├── fetch/
│   │   ├── __init__.py
│   │   ├── http_fetch.py       # HTTPFetch
│   └── llm/
│       ├── __init__.py
│       └── litellm_provider.py # LiteLLMProvider wrapping litellm
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py        # Abstract Strategy base class
│   ├── scratchpad_strategy.py  # Scratchpad implementation
│   └── graph_reader_strategy.py # GraphReader implementation
├── utils.py                    # Utility functions (cost tracking, parsing, etc)

```

---

## Implementation Phases

### Phase 1: Core Types & Providers (Foundation)
**Files**: `types.py`, `providers/*`, `implementations/*`

1. **Types Module** (`types.py`)
   - `SearchResult(title, url, snippet)`
   - `LLMResponse(text, cost, reasoning)`
   - `Result(answer, cost, knowledge)`
   - `Scratchpad(question)` - with snapshot() method
   - `AtomicFact(fact, source)`
   - `Notebook()` - with addFact(), deduplication logic, serialization

2. **Provider Abstractions** (Abstract base classes)
   - `LLMProvider` - abstract `generate(system_prompt, user_prompt)` → `LLMResponse`
   - `SearchProvider` - abstract `search(query)` → `List[SearchResult]`
   - `FetchProvider` - abstract `fetch(url)` → `str`

3. **LLM Implementation** (`implementations/llm/litellm_provider.py`)
   - Wrap litellm.completion() to use AgentShiro's existing model support
   - Track costs per model (using litellm's token counting)
   - Reuse ANTHROPIC_API_KEY / OPENAI_API_KEY from AgentShiro's config

4. **Search Implementations**
   - `DuckDuckGoSearch` - free, no API key

5. **Fetch Implementation** (`implementations/fetch/http_fetch.py`)
   - Simple HTML stripper using BeautifulSoup or regex
   - Error handling & timeouts

---

### Phase 2: Prompts & Core Agent (Logic)
**Files**: `prompts.py`, `agent.py`

1. **Prompts Module** (`prompts.py`)
   ```python
   PLANNER_SYSTEM = "You are a focused research planner..."
   SYNTHESIZER_SYSTEM = "You are a research synthesizer..."
   FINALIZER_SYSTEM = "You are a research finalizer..."
   EXTRACTOR_SYSTEM = "You are a fact extractor..."
   NEIGHBOR_SYSTEM = "You are a query generator..."
   ```

2. **ResearchAgent Class** (`agent.py`)
   - Extend `agentshiro.Agent`
   - Constructor:
     ```python
     def __init__(self, model_name: str, 
                  strategy: str = "scratchpad",
                  llm_provider: LLMProvider = None,
                  search_provider: SearchProvider = None,
                  fetch_provider: FetchProvider = None,
                  max_iterations: int = 5,
                  tools: List[BaseTool] = None)
     ```
   - Method: `answer(question, knowledge="") → Result`
   - Uses Strategy pattern to delegate to ScratchpadStrategy or GraphReaderStrategy
   - LLM calls use litellm (via LiteLLMProvider wrapper)
   - Automatic session & observability logging (inherited from Agent)

---

### Phase 3: Strategies (Algorithms)
**Files**: `strategies/base_strategy.py`, `strategies/scratchpad_strategy.py`, `strategies/graph_reader_strategy.py`

1. **Base Strategy** (`base_strategy.py`)
   ```python
   class Strategy(ABC):
       @abstractmethod
       def answer(self, question: str) -> Result:
           pass
   ```

2. **Scratchpad Strategy** (`scratchpad_strategy.py`)
   - Loop up to max_iterations:
     1. Planner decides: "Action: Answer" or "Action: Search\nQuery: ..."
     2. If Answer → break
     3. If Search → execute search, synthesize results
     4. Update scratchpad knowledge
   - Finalizer produces answer
   - Return Result with cost tracking

3. **Graph Reader Strategy** (`graph_reader_strategy.py`)
   - Initial planning: break question into key elements, generate 3-5 queries
   - Queue-based processing (BFS):
     - Search each query
     - Extract atomic facts into Notebook
     - Check if answerable (heuristic: >= 5 facts)
     - Generate neighbor queries to fill gaps
     - Continue until max steps or facts sufficient
   - Finalizer produces answer
   - Return Result with knowledge = notebook.toJSON()

---

### Phase 4: Utilities
**Files**: `utils.py`, `example.py`,

1. **Utils** (`utils.py`)
   - Parsing helpers (e.g., `parse_planner_decision()`, `extract_queries()`)
   - Cost calculation helpers
   - Logging utilities


## Integration with AgentShiro

### What We Reuse
- ✅ `Agent` base class (for session management, message history)
- ✅ `SessionManager` (for saving/loading conversations)
- ✅ `run_agent_loop()` can potentially wrap research logic
- ✅ `litellm.completion()` for LLM calls
- ✅ Tool system (if we add search/fetch as tools)

### What's Different
- ResearchAgent is **specialized** for research workflows (not general chat)
- Uses **provider abstractions** (not direct litellm calls)
- Uses **strategies** (pluggable research algorithms)
- Optimized for **cost tracking** and **fact accumulation**

---

## Data Flow

### Scratchpad Example
```
User Question: "Why is the sky blue?"
       ↓
ResearchAgent.answer(question)
       ↓
ScratchpadStrategy.answer()
       ↓
Iteration 1:
  Planner: "Action: Search\nQuery: why is the sky blue"
  Searcher: [SearchResult(...), ...]
  Synthesizer: "Rayleigh scattering causes..."
  Update Scratchpad.knowledge
       ↓
Iteration 2:
  Planner: "Action: Answer"  ← sufficient knowledge
  Break
       ↓
Finalizer: "The sky appears blue due to Rayleigh scattering..."
       ↓
Result(answer="...", cost=0.015, knowledge="Rayleigh scattering...")
```

### Graph Reader Example
```
User Question: "Benefits of renewable energy and leading countries?"
       ↓
Planner: Break into elements & generate 3-5 initial queries
  Queue: ["renewable energy benefits", "solar energy adoption", "wind power leaders", ...]
       ↓
While queue not empty (max 8 steps):
  Pop query from queue
  Search → [SearchResult, ...]
  Extractor → atomic facts
  Notebook.addFact(fact, source)
  Check if answerable (>= 5 facts)?
  If yes → break
  If no → Neighbor generates new queries → add to queue
       ↓
Finalizer: Synthesize notebook facts into answer
       ↓
Result(answer="...", cost=0.50, knowledge=notebook.toJSON())
```

---

## Configuration & Usage Example

```python
from research_agent import ResearchAgent
from research_agent.implementations.search import DuckDuckGoSearch
from research_agent.implementations.llm import LiteLLMProvider

# Initialize
agent = ResearchAgent(
    model_name="claude-3-5-sonnet-20241022",  # Uses litellm
    strategy="scratchpad",
    llm_provider=LiteLLMProvider(),
    search_provider=DuckDuckGoSearch(),
    max_iterations=5
)

# Answer a question
result = agent.answer("Who won the 2024 Nobel Prize in Chemistry?")

print(f"Answer: {result.answer}")
print(f"Cost: ${result.cost:.4f}")
print(f"Knowledge: {result.knowledge}")
```

---


## Success Criteria

- [x] Both Scratchpad and GraphReader strategies implemented
- [x] Cost tracking per query
- [x] Fact deduplication in Notebook
- [x] Session management (inherited from Agent)
- [x] Works with litellm models
- [x] DuckDuckGo search integration
- [x] Extensible provider system
- [x] Example scripts demonstrating usage

---

## Timeline Estimate

- **Phase 1** (Types & Providers): ~2-3 hours
- **Phase 2** (Prompts & Agent): ~1-2 hours
- **Phase 3** (Strategies): ~3-4 hours
- **Phase 4** (Utils & Tests): ~1-2 hours
- **Total**: ~7-11 hours of implementation

---

## Notes

- The implementation closely mirrors the Node.js design while adapting to Python idioms and AgentShiro's architecture
- Async support can be added later if needed
- Cost calculation uses litellm's token estimator
- The `Notebook` serialization (JSON) allows knowledge sharing between queries
