
## 🎯 **tau2-bench: Complete In-Depth Explanation**

τ²-bench (tau-squared-bench) is a **benchmark framework for evaluating conversational AI agents** in real-world customer service scenarios. It tests how well LLM-powered agents handle complex, multi-step interactions with tools while following policies and meeting user needs.

---

## 📋 **What Is It & Why We Need It**

### **The Problem**
Traditional LLM benchmarks test general knowledge (QA, factual accuracy). But production agents need to:
- Use **multiple tools correctly** (book flights, update orders, process refunds)
- **Follow organizational policies** (refund limits, escalation rules)
- **Communicate effectively** with users
- **Maintain database integrity** (don't corrupt customer records)

τ²-bench tests all of these simultaneously.

### **The Solution**
τ²-bench creates a **simulation environment** where:
1. An **LLM Agent** acts as a customer service representative
2. A **User Simulator** (also LLM-powered) plays the customer
3. The system **evaluates performance** across multiple dimensions
4. Results show **exactly why** the agent succeeded or failed

---

## 🏗️ **Core Architecture**

### **Key Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    τ²-Bench Framework                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DOMAINS (Airline, Retail, Telecom, Banking)            │
│     ├── Policy (rules agent must follow)                    │
│     ├── Tools (functions agent can call)                    │
│     ├── Database (simulated system state)                   │
│     └── Tasks (test scenarios with gold standards)          │
│                                                              │
│  2. ORCHESTRATOR                                            │
│     ├── Half-Duplex Mode (turn-by-turn text)               │
│     └── Full-Duplex Mode (simultaneous voice)              │
│                                                              │
│  3. EVALUATORS (scoring)                                    │
│     ├── Environment Evaluator (DB state correct?)           │
│     ├── Action Evaluator (right tools called?)              │
│     ├── Communicate Evaluator (info conveyed?)              │
│     └── NL Assertions (LLM judges qualitative aspects)     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **Available Domains (Real-World Scenarios)**

| Domain | Tasks | Tools | Example |
|--------|-------|-------|---------|
| **Airline** | Flight booking, cancellations, rebooking | `book_flight`, `cancel_booking`, `view_itinerary` | Customer wants to change flight date |
| **Retail** | Order management, returns, inquiries | `place_order`, `initiate_return`, `track_order` | Customer requests refund for damaged item |
| **Telecom** | Account management, troubleshooting | `update_plan`, `check_balance`, `fix_connectivity` | Customer has billing issue |
| **Banking Knowledge** | Customer service with document retrieval | `search_docs`, `explain_policy`, `process_request` | Customer asks about loan terms |

---

## 🔄 **How It Works: Complete Flow**

### **Step 1: Task Definition**

Each task is a JSON specification with:

```json
{
  "task_id": "airline_001",
  "domain": "airline",
  "user_instruction": "Book a flight from NYC to LAX for 2 people on Dec 25. You have budget $800 per ticket.",
  "expected_actions": [
    {"tool": "search_flights", "args": {"from": "NYC", "to": "LAX", "date": "2024-12-25"}},
    {"tool": "book_flight", "args": {"flight_id": "AA123", "passengers": 2}}
  ],
  "expected_communication": [
    "Confirm the booking reference",
    "Provide total cost"
  ],
  "policy_constraints": [
    "Must confirm passenger details before booking",
    "Cannot exceed budget per ticket"
  ],
  "evaluation_criteria": {
    "actions": [...],              // Actions to check
    "communicate_info": [...],     // Info to communicate
    "env_assertions": [...]        // Database state checks
  }
}
```

### **Step 2: Simulation Execution**

```
┌─────────────────────────────────────────────────────────────┐
│                  Simulation Turn 1                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  USER SIMULATOR:                                             │
│  "Hi, I want to book a flight NYC→LAX for 2, budget $800"   │
│                                                              │
│  ↓ (sent to Agent)                                          │
│                                                              │
│  AGENT LLM:                                                  │
│  - Reads: Policy, User Message, Available Tools             │
│  - Calls: search_flights("NYC", "LAX", "2024-12-25")       │
│  - Response: [Flight AA123: $750/ticket ✓ in budget]       │
│  - Asks: "Confirm passenger names?"                         │
│                                                              │
│  ↓ (sent to User Simulator)                                │
│                                                              │
│  USER SIMULATOR:                                             │
│  "Passenger 1: John Doe. Passenger 2: Jane Smith"          │
│                                                              │
│  ... (continues for multiple turns until task complete)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### **Step 3: Evaluation (Multi-Dimensional Scoring)**

After the conversation ends, **4 independent evaluators** score the agent:

---

## 📈 **Evaluation System (How They Score)**

### **1. Environment Evaluator** ✅ (Database State)

**What it checks:** Did the agent's actions result in the correct database state?

```python
# After agent calls book_flight(), the evaluator:

1. Extracts all tool calls from trajectory
2. Replays them in a fresh database
3. Compares final state with "gold standard"

# Example:
Gold State: {
  "flights": [...],
  "bookings": [{
    "booking_id": "B123",
    "passengers": ["John Doe", "Jane Smith"],
    "total_cost": 1500,
    "status": "CONFIRMED"
  }]
}

Agent's Result State: {...same...} ✓

Score: 1.0 (PASS) or 0.0 (FAIL)
```

**Reward Type:** `DB` or `ENV_ASSERTION`

---

### **2. Action Evaluator** ✅ (Tool Calls)

**What it checks:** Did the agent call the RIGHT tools with the RIGHT arguments?

```python
# Task expects:
expected_actions = [
    Action(tool="search_flights", params={"from": "NYC", "to": "LAX"}),
    Action(tool="book_flight", params={"flight_id": "AA123", "passengers": 2})
]

# Agent actually called:
agent_actions = [
    Action(tool="search_flights", params={"from": "NYC", "to": "LAX"}),  ✓
    Action(tool="book_flight", params={"flight_id": "AA123", "passengers": 2})  ✓
]

# Matching logic:
- Exact match: ✓
- All expected actions present: ✓
- No unexpected actions blocking: ✓

Score: 1.0 (PASS) or 0.0 (FAIL)
```

**Reward Type:** `ACTION`

---

### **3. Communicate Evaluator** ✅ (Information Conveyed)

**What it checks:** Did the agent tell the user the REQUIRED information?

```python
# Task specifies user needs to know:
required_info = [
    "Booking confirmation number",
    "Total cost of $1500",
    "Departure time and date"
]

# Agent's messages to user:
messages = [
    "Your booking reference is B123-XYZ",           ✓ (confirms #1)
    "Total cost: $1,500 for 2 passengers",          ✓ (confirms #2)
    "You depart Dec 25 at 10:15 AM from JFK",      ✓ (confirms #3)
]

# Evaluation:
- Check if each required info appears in agent messages (text matching/NLP)
- All required info present: ✓

Score: 1.0 (PASS) or 0.0 (FAIL)
```

**Reward Type:** `COMMUNICATE`

---

### **4. NL Assertions Evaluator** ✅ (LLM Judge - Qualitative)

**What it checks:** Does the agent's BEHAVIOR match qualitative criteria? (Experimental/WIP)

```python
# Task specifies:
nl_assertions = [
    "Agent was polite and professional",
    "Agent handled customer concerns empathetically",
    "Agent didn't hallucinate prices or flights"
]

# LLM Judge evaluates:
Prompt: """
Conversation:
[full agent-user conversation]

Assertion: "Agent was polite and professional"
Did the agent meet this? Yes/No + Reasoning
"""

# Judge Response:
{
    "assertion": "Agent was polite and professional",
    "met": true,
    "reasoning": "Agent used courteous language, apologized for wait times..."
}

Score: 1.0 (assertion met) or 0.0 (failed)
```

**Reward Type:** `NL_ASSERTION`

---

### **How Scores Combine**

The **final reward is multiplicative**:

```
Final Reward = DB_score × ACTION_score × COMMUNICATE_score × NL_score

If ANY component = 0, final = 0
Example:
- DB: 1.0 ✓
- ACTION: 0.0 ✗ (missed a required tool call)
- COMMUNICATE: 1.0 ✓
- NL: 1.0 ✓

Final = 1.0 × 0.0 × 1.0 × 1.0 = 0.0 (FAIL)
```

Each domain specifies which evaluators matter via `reward_basis`:

```python
# Example airline task reward_basis
reward_basis = ["DB", "ACTION", "COMMUNICATE"]  # NL not required
```

---

## 📦 **Dataset Structure**

Each domain folder contains:

```
data/tau2/domains/airline/
├── tasks.json                # 50-100 customer service scenarios
├── tasks_voice.json          # Same tasks optimized for voice
├── split_tasks.json          # Train/test/eval splits
├── policy.md                 # Rules agent must follow
├── db.json                   # Initial database state
├── user_db.json              # User simulator parameters (optional)
└── agents/
    ├── tools.py              # search_flights, book_flight, etc.
    └── user_tools.py         # Tools for user simulator (e.g., confirm payment)
```

### **Example Task**

```json
{
  "task_id": "airline_042",
  "description": "Customer booked wrong flight, needs to change",
  "user_instruction": "I accidentally booked flight AA500 for tomorrow but I meant to book AA501 (same route, 2 hours later). Please help me change it.",
  "policy": {
    "change_allowed": true,
    "change_fee": 50,
    "restrictions": "Can only change if within 24 hours of departure"
  },
  "evaluation_criteria": {
    "actions": [
      {"tool": "view_booking", "expected": true},
      {"tool": "verify_change_eligibility", "expected": true},
      {"tool": "process_flight_change", "expected": true}
    ],
    "communicate_info": [
      "Change fee amount",
      "New flight confirmation",
      "Updated departure time"
    ],
    "env_assertions": [
      "Old booking marked CANCELLED",
      "New booking created with AA501",
      "Customer account charged $50 change fee"
    ]
  }
}
```

---

## 🎬 **Complete Execution Example**

### **Example: Airline Booking Task**

```bash
# Run the benchmark
tau2 run --domain airline \
         --agent-llm gpt-4 \
         --user-llm gpt-4 \
         --num-tasks 5 \
         --num-trials 3
```

**What happens:**

```
Task: airline_042 (Change flight booking)
Trial 1 of 3
─────────────────────────────────────────────

TURN 1
─────
User Simulator → Agent:
  "Hi, I accidentally booked flight AA500 for tomorrow but meant AA501. 
   Can you help me change it?"

Agent LLM (reading policy + tools):
  📋 Policy: Flight changes allowed within 24 hours, $50 fee
  🛠️ Available: view_booking, verify_change_eligibility, process_flight_change
  
  "I can help with that! Let me check your booking first."
  [CALL: view_booking(booking_id="B542")]
  
User Simulator receives tool result:
  {booking: "AA500 tomorrow 2PM, reference: B542"}
  
User Simulator → Agent:
  "Yes, that's the wrong flight."

TURN 2
─────
Agent: "Let me verify you're eligible for a change..."
  [CALL: verify_change_eligibility(booking_id="B542")]

Tool Result: {eligible: true, fee: 50}

Agent: "Good news! You can change it. There's a $50 change fee. 
        Should I proceed?"

User Simulator → Agent:
  "Yes, go ahead."

TURN 3
─────
Agent: "Processing your change to flight AA501..."
  [CALL: process_flight_change(
    booking_id="B542",
    new_flight_id="AA501",
    fee=50
  )]

Tool Result: {status: "CONFIRMED", new_reference: "B943"}

Agent: "Done! Your new booking reference is B943. 
        AA501 departs tomorrow at 4:15 PM. The $50 change fee has been charged."

User Simulator: "Perfect, thanks!"
Agent: "You're welcome!"

[Conversation Ends - User Satisfied]

─────────────────────────────────────────────
EVALUATION
─────────────────────────────────────────────

1️⃣  ENVIRONMENT EVALUATOR
   ✓ Old booking marked CANCELLED
   ✓ New booking (AA501) created
   ✓ Change fee ($50) deducted from account
   Score: 1.0

2️⃣  ACTION EVALUATOR
   Expected actions:
   ✓ view_booking (called)
   ✓ verify_change_eligibility (called)
   ✓ process_flight_change (called)
   Score: 1.0

3️⃣  COMMUNICATE EVALUATOR
   Required info:
   ✓ "Change fee amount" → Agent said "$50 change fee"
   ✓ "New flight confirmation" → Agent said "AA501"
   ✓ "Updated departure time" → Agent said "4:15 PM tomorrow"
   Score: 1.0

4️⃣  NL ASSERTIONS EVALUATOR
   ✓ "Agent was courteous" → Yes
   ✓ "Agent verified eligibility before processing" → Yes
   ✓ "Agent didn't hallucinate policy details" → Yes
   Score: 1.0

─────────────────────────────────────────────
FINAL REWARD = 1.0 × 1.0 × 1.0 × 1.0 = 1.0 ✅ PASS
─────────────────────────────────────────────

Metrics:
- Conversation turns: 3
- Tool calls: 3 (all correct)
- Agent tokens: 456
- Cost: $0.02
```

---

## 🎙️ **Communication Modes**

### **Half-Duplex (Text, Turn-Based)** 📝
```
Turn 1: User sends message → Agent responds with message + tool calls
Turn 2: Tools return results → Agent processes → User responds
... (sequential, explicit turns)
```

### **Full-Duplex (Voice, Simultaneous)** 🎵
```
User speaks continuously
Agent listens and speaks simultaneously (realtime providers like OpenAI Realtime)
More realistic but harder to evaluate
```

---

## 🎯 **Features of τ²-bench**

| Feature | Details |
|---------|---------|
| **Multi-modal** | Text (half-duplex) + Voice (full-duplex) + Knowledge retrieval |
| **5 Domains** | Airline, Retail, Telecom, Banking, Mock (test domain) |
| **4 Evaluators** | Environment, Action, Communicate, NL Assertions |
| **Configurable** | Switch LLMs, domains, task counts |
| **Reproducible** | Golden standards prevent evaluation drift |
| **Leaderboard** | Submit results to taubench.com |
| **Extensible** | Build custom agents, add new domains |
| **Open Source** | MIT licensed, 1000+ stars |

---

## 💡 **Why This Matters**

**Without τ²-bench:**
- "Is my agent good?" → Run it on a few chats, hope for the best
- Don't know WHERE it fails (tool use? communication? policy?)
- Can't compare fairly between models
- Manual evaluation is tedious and inconsistent

**With τ²-bench:**
- "Agent scored 0.87 on airline tasks" → Precise, reproducible metric
- Breakdown shows: 0.95 on DB state, 0.85 on tool use, 0.92 on communication
- Compare GPT-4 vs Claude vs open-source fairly
- 100+ tasks, automated evaluation, detailed error analysis

---

## 🚀 **Quick Start**

```bash
# Install
git clone https://github.com/sierra-research/tau2-bench
cd tau2-bench
uv sync

# Run evaluation
cp .env.example .env
# [Add your API keys]

tau2 run --domain airline \
         --agent-llm gpt-4 \
         --user-llm gpt-4 \
         --num-tasks 10

# View results
tau2 view
```

---

## 📚 **Dataset Contents Summary**

- **Total tasks:** 1000+ across 5 domains
- **Task types:** Booking, cancellation, troubleshooting, refunds, policy questions
- **Difficulty:** Easy → Complex multi-step scenarios
- **Splits:** `base` (full eval set), `train`, `test`, `validation`
- **Voice tasks:** 75+ speech variations for audio evaluation
- **Knowledge domain:** 700+ banking documents for retrieval testing

This makes τ²-bench a **production-grade benchmark** for evaluating LLM agents in real-world scenarios! 🎯