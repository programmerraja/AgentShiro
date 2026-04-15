# Life-Assistant Test Framework

Comprehensive evaluation framework for testing the Life-Assistant agent using LLM-based user simulation and LLM-based judge evaluation.

## Architecture Overview

```
test_cases.json (5 test cases)
    ↓
evaluator.py (TestRunner)
    ├─ StateManager: Setup/teardown test life-system
    ├─ UserAgent: LLM that simulates user behavior
    ├─ ConversationRunner: Orchestrates user-assistant conversation
    ├─ JudgeLLM: LLM that evaluates conversation
    └─ ResultsCollector: Saves results and reports
    ↓
test_runs/ (Results for each test)
    ├─ test_TC-1.1/
    │   ├─ life-system/ (Copy of template with test state)
    │   ├─ conversation.json
    │   ├─ judge_scores.json
    │   ├─ result.json
    │   └─ report.md
    └─ summary_report.json (Aggregate results)
```

## Components

### 1. **test_cases.json**
Defines 5 diverse test cases:
- **TC-1.1**: Simple task addition (basic functionality)
- **TC-1.3**: Conflicting task (alignment detection)
- **TC-3.2**: Progress tracking query (reflection quality)
- **TC-4.1**: End of day reporting (gamification)
- **TC-7.3**: Duplicate detection (edge case handling)

Each test case includes:
- Initial state (files to create, current date/time)
- User agent prompt (detailed instructions)
- Ground truth (expected behaviors)
- Safeguards (max turns, timeout)

### 2. **StateManager**
- Copies `template_life_system/` for each test
- Creates initial state files from JSON
- Isolates each test's file operations

### 3. **UserAgent**
- LLM instance that simulates user behavior
- Receives detailed prompt from test case
- Only sees assistant's text responses (not tool calls)
- Calls `[END]` when goal is achieved
- Runs until: end called, max turns, or timeout

### 4. **ConversationRunner**
- Orchestrates turn-by-turn conversation
- Manages safeguards (max 15 turns, 300s timeout)
- Extracts tool calls and responses
- Tracks conversation for judge evaluation

### 5. **JudgeLLM**
Evaluates conversation across 4 LAB dimensions:
- **Tool Accuracy** (0-1): Correct tool calls with right args?
- **Alignment Detection** (0-1): Correct task alignment counts?
- **Planning Quality** (0-1): Realistic, actionable schedules?
- **Reflection Quality** (0-1): Meaningful, pattern-based insights?

Weighted Score = (0.25 × each dimension)

### 6. **ResultsCollector**
- Saves conversation history
- Saves judge scores and reasoning
- Generates human-readable reports
- Aggregates all test results

## Running Tests

```bash
python run_tests.py
```

Output:
- Console: Real-time progress with scores
- test_runs/: Detailed results per test
- test_runs/summary_report.json: Aggregate metrics

## Test Case Design

### Example: TC-1.1 (Simple Task Addition)

**Initial State:**
- Today: 2026-04-14
- No daily file exists yet
- Gamification: 100 points, streak 3

**User Prompt:**
"You need to buy milk. Add it to your daily plan. When asked for time, say 'Evening'."

**Expected Behaviors:**
- Ask for task time
- Read today's daily file (creates if missing)
- Write task to file
- No alignment check (too small/neutral task)

**Ground Truth:**
- Must call: readFile, writeFile
- Must not call: readFile of areas/
- Result: Task added at ~6 PM

**Judge Evaluation:**
- Tool Accuracy: 1.0 if readFile+writeFile correct
- Planning Quality: 1.0 if time is actionable
- Alignment Detection: N/A (no conflict)
- Reflection Quality: N/A (no reflection needed)

## Adding New Test Cases

1. Edit `test_cases.json`
2. Add entry with:
   ```json
   {
     "test_id": "TC-X.X",
     "title": "...",
     "initial_state": {...},
     "user_agent_prompt": "...",
     "ground_truth": {...},
     "safeguards": {...}
   }
   ```
3. Run: `python run_tests.py`

## Modifying Existing Tests

To update TC-1.1:
1. Edit initial_state to change preconditions
2. Edit user_agent_prompt to change user behavior
3. Edit ground_truth to update expectations
4. Run tests again

## Safeguards

Each test has:
- **max_turns**: Stop after N turns (default: 15)
- **timeout_seconds**: Stop after timeout (default: 300)
- **required_tool_calls**: Expect end tool to be called

Prevents:
- Infinite loops
- Runaway conversations
- Tests taking too long

## Scoring Interpretation

- **0.8+**: Excellent pass
- **0.6-0.8**: Good pass
- **0.4-0.6**: Weak pass
- **<0.4**: Fail

## Troubleshooting

**Tool calls not working:**
- Check that test_runs/test_X/life-system/ exists
- Verify file paths in tools are correct
- Check tool base_dir is set properly

**User agent loops:**
- Increase max_turns safeguard
- Check user prompt clarity
- Review test case setup

**Low judge scores:**
- Review conversation flow
- Check if agent detected conflicts correctly
- Verify reflection quality in responses

## Future Enhancements

- [ ] Integration with CI/CD
- [ ] Performance metrics per mode (Planner vs Analyzer)
- [ ] Visualization of results
- [ ] Comparison between model versions
- [ ] Auto-generation of test cases from simulator.md
- [ ] Better error categorization
