Let me create comprehensive Node.js code for a Laconic-like research agent:

## 1. **Core Types & Interfaces**

```javascript
// types.js

// Search result from search provider
class SearchResult {
  constructor(title, url, snippet) {
    this.title = title;
    this.url = url;
    this.snippet = snippet;
  }
}

// LLM response with cost tracking
class LLMResponse {
  constructor(text, cost = 0, reasoning = "") {
    this.text = text;
    this.cost = cost;
    this.reasoning = reasoning;
  }
}

// Final result from agent
class Result {
  constructor(answer, cost = 0, knowledge = "") {
    this.answer = answer;
    this.cost = cost;
    this.knowledge = knowledge;
  }
}

// Scratchpad state
class Scratchpad {
  constructor(question) {
    this.originalQuestion = question;
    this.currentStep = "";
    this.knowledge = "";
    this.history = [];
    this.iterationCount = 0;
  }

  snapshot() {
    return `Question: 
${this.originalQuestion}

Current Step:
${this.currentStep || "(none yet)"}

Knowledge:
${this.knowledge?.trim() || "(empty)"}

History:
${this.history.length > 0 ? this.history.join("\n") : "(none)"}

Iteration: ${this.iterationCount}`;
  }

  appendHistory(entry) {
    if (entry) this.history.push(entry);
  }
}

// Graph Reader state - atomic facts
class AtomicFact {
  constructor(fact, source) {
    this.fact = fact;
    this.source = source;
  }
}

class Notebook {
  constructor() {
    this.facts = [];
  }

  addFact(fact, source) {
    // Dedup: check if exact match or substring already exists
    const newFact = new AtomicFact(fact, source);
    const isDuplicate = this.facts.some(
      f => f.fact === fact || fact.includes(f.fact) || f.fact.includes(fact)
    );
    if (!isDuplicate) {
      this.facts.push(newFact);
    }
  }

  toJSON() {
    return JSON.stringify(this.facts, null, 2);
  }

  static fromJSON(jsonStr) {
    const notebook = new Notebook();
    const data = JSON.parse(jsonStr);
    data.forEach(item => {
      notebook.facts.push(new AtomicFact(item.fact, item.source));
    });
    return notebook;
  }
}

module.exports = {
  SearchResult,
  LLMResponse,
  Result,
  Scratchpad,
  AtomicFact,
  Notebook,
};
```

---

## 2. **LLM Provider (Abstract Interface)**

```javascript
// llmProvider.js

/**
 * Abstract LLM Provider - implement this with your favorite model
 * Examples: OpenAI, Ollama, Anthropic, etc.
 */
class LLMProvider {
  async generate(systemPrompt, userPrompt) {
    throw new Error("Must implement generate()");
  }
}

/**
 * Example: Ollama Local LLM
 */
class OllamaLLM extends LLMProvider {
  constructor(model = "mistral", endpoint = "http://localhost:11434") {
    super();
    this.model = model;
    this.endpoint = endpoint;
  }

  async generate(systemPrompt, userPrompt) {
    try {
      const response = await fetch(`${this.endpoint}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: this.model,
          prompt: `${systemPrompt}\n\n${userPrompt}`,
          stream: false,
        }),
      });

      const data = await response.json();
      const { LLMResponse } = require("./types");
      return new LLMResponse(data.response, 0); // Ollama is free locally
    } catch (error) {
      throw new Error(`Ollama error: ${error.message}`);
    }
  }
}

/**
 * Example: OpenAI
 */
class OpenAILLM extends LLMProvider {
  constructor(apiKey, model = "gpt-4o") {
    super();
    this.apiKey = apiKey;
    this.model = model;
  }

  async generate(systemPrompt, userPrompt) {
    try {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: this.model,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt },
          ],
          temperature: 0.7,
        }),
      });

      const data = await response.json();
      const { LLMResponse } = require("./types");
      const cost = this.calculateCost(data.usage);
      return new LLMResponse(data.choices[0].message.content, cost);
    } catch (error) {
      throw new Error(`OpenAI error: ${error.message}`);
    }
  }

  calculateCost(usage) {
    // Rough pricing for gpt-4o: $0.075/1M input, $0.30/1M output
    const inputCost = (usage.prompt_tokens / 1000000) * 0.075;
    const outputCost = (usage.completion_tokens / 1000000) * 0.30;
    return inputCost + outputCost;
  }
}

/**
 * Example: Mock LLM (for testing)
 */
class MockLLM extends LLMProvider {
  constructor(responses = {}) {
    super();
    this.responses = responses;
    this.callCount = 0;
  }

  async generate(systemPrompt, userPrompt) {
    const { LLMResponse } = require("./types");
    
    // Return hardcoded responses for testing
    if (systemPrompt.includes("planner")) {
      return new LLMResponse("Action: Search\nQuery: why is the sky blue", 0.001);
    }
    if (systemPrompt.includes("synthesizer")) {
      return new LLMResponse(
        "Rayleigh scattering makes the sky appear blue.",
        0.001
      );
    }
    return new LLMResponse("The sky is blue due to Rayleigh scattering.", 0.002);
  }
}

module.exports = {
  LLMProvider,
  OllamaLLM,
  OpenAILLM,
  MockLLM,
};
```

---

## 3. **Search Provider**

```javascript
// searchProvider.js

/**
 * Abstract Search Provider
 */
class SearchProvider {
  async search(query) {
    throw new Error("Must implement search()");
  }
}

/**
 * DuckDuckGo (Free, no API key)
 */
class DuckDuckGoSearch extends SearchProvider {
  async search(query) {
    try {
      const url = `https://html.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json`;
      const response = await fetch(url);
      const data = await response.json();

      // Parse DuckDuckGo response
      const { SearchResult } = require("./types");
      return data.Results.map(
        (r) => new SearchResult(r.Title, r.FirstURL, r.Text)
      ).slice(0, 5); // Return top 5
    } catch (error) {
      console.error(`DuckDuckGo search error: ${error.message}`);
      return [];
    }
  }
}

/**
 * Brave Search (requires API key)
 */
class BraveSearch extends SearchProvider {
  constructor(apiKey) {
    super();
    this.apiKey = apiKey;
  }

  async search(query) {
    try {
      const response = await fetch("https://api.search.brave.com/res/v1/web/search", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Subscription-Token": this.apiKey,
        },
        body: JSON.stringify({ q: query }),
      });

      const data = await response.json();
      const { SearchResult } = require("./types");

      return (data.web || [])
        .map((r) => new SearchResult(r.title, r.url, r.description))
        .slice(0, 5);
    } catch (error) {
      console.error(`Brave search error: ${error.message}`);
      return [];
    }
  }
}

/**
 * Mock Search (for testing)
 */
class MockSearch extends SearchProvider {
  constructor(mockResults = []) {
    super();
    this.mockResults = mockResults;
  }

  async search(query) {
    // Return mock results
    return this.mockResults;
  }
}

module.exports = {
  SearchProvider,
  DuckDuckGoSearch,
  BraveSearch,
  MockSearch,
};
```

---

## 4. **Fetch Provider (for deep reading)**

```javascript
// fetchProvider.js

class FetchProvider {
  async fetch(url) {
    throw new Error("Must implement fetch()");
  }
}

class HTTPFetch extends FetchProvider {
  async fetch(url) {
    try {
      const response = await fetch(url);
      const text = await response.text();
      
      // Simple HTML stripping
      return text
        .replace(/<script[^>]*>.*?<\/script>/gs, "")
        .replace(/<style[^>]*>.*?<\/style>/gs, "")
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
    } catch (error) {
      console.error(`Fetch error: ${error.message}`);
      return "";
    }
  }
}

module.exports = { FetchProvider, HTTPFetch };
```

---

## 5. **Scratchpad Strategy (Simple Loop)**

```javascript
// strategies/scratchpadStrategy.js

const { Scratchpad, Result } = require("../types");

// Prompts
const PLANNER_SYSTEM = `You are a focused research planner. 
Your job is to decide whether we have enough information to answer the user's question, or if we need to search for more.

Respond with EXACTLY one of:
- "Action: Answer" (if we have enough info)
- "Action: Search\nQuery: <specific search query>" (if we need more info)

Be concise. No explanations, just the action.`;

const SYNTHESIZER_SYSTEM = `You are a research synthesizer. 
Take the current knowledge and the new search results, and produce a concise summary.
Keep only facts that directly help answer the original question.
Be factual and clear. One paragraph maximum.`;

const FINALIZER_SYSTEM = `You are a research finalizer. 
Take the collected knowledge and produce a clear, comprehensive answer to the user's question.
Be specific and reference the facts you have.`;

class ScratchpadStrategy {
  constructor(agent) {
    this.agent = agent;
  }

  name() {
    return "scratchpad";
  }

  async answer(question) {
    const pad = new Scratchpad(question);
    let totalCost = 0;
    const maxIterations = this.agent.maxIterations || 5;

    console.log(`\n📝 Starting Scratchpad Strategy (max ${maxIterations} iterations)`);

    // Main loop
    for (let i = 0; i < maxIterations; i++) {
      pad.iterationCount = i + 1;
      console.log(`\n--- Iteration ${pad.iterationCount} ---`);
      console.log(`Scratchpad snapshot:\n${pad.snapshot()}\n`);

      // Step 1: Planner decides
      console.log("🤔 Planner analyzing...");
      const plannerResp = await this.agent.planner.generate(
        PLANNER_SYSTEM,
        pad.snapshot()
      );
      totalCost += plannerResp.cost;
      console.log(`Planner response: ${plannerResp.text}`);

      const decision = this.parsePlannerDecision(plannerResp.text);

      if (decision.action === "Answer") {
        console.log("✅ Planner decided we have enough info!");
        break;
      }

      // Step 2: Search
      console.log(`🔍 Searching for: "${decision.query}"`);
      const searchResults = await this.agent.searcher.search(decision.query);
      totalCost += (searchResults.length * this.agent.searchCost) || 0;

      if (searchResults.length === 0) {
        console.log("⚠️  No search results found");
        pad.appendHistory(`Search for "${decision.query}" returned 0 results`);
        continue;
      }

      console.log(`Found ${searchResults.length} results`);
      searchResults.forEach((r, idx) => {
        console.log(`  ${idx + 1}. ${r.title} (${r.url})`);
      });

      // Step 3: Synthesizer compresses results
      console.log("📚 Synthesizing results...");
      const synthesizerPrompt = `
Current Question: ${pad.originalQuestion}

Current Knowledge:
${pad.knowledge || "(empty)"}

New Search Results:
${searchResults.map((r, i) => `${i + 1}. Title: ${r.title}\nSnippet: ${r.snippet}`).join("\n\n")}

Please synthesize this into a concise knowledge summary.`;

      const synthResp = await this.agent.synthesizer.generate(
        SYNTHESIZER_SYSTEM,
        synthesizerPrompt
      );
      totalCost += synthResp.cost;

      pad.knowledge = synthResp.text;
      pad.currentStep = `Last query: ${decision.query}`;
      pad.appendHistory(`Search & synthesize: "${decision.query}"`);

      console.log(`Updated knowledge: ${pad.knowledge.substring(0, 100)}...`);
    }

    // Step 4: Finalizer produces answer
    console.log("\n✍️  Finalizer producing answer...");
    const finalizerPrompt = `
Question: ${pad.originalQuestion}

Collected Knowledge:
${pad.knowledge || "(no knowledge gathered)"}

Please provide a clear, direct answer based on the knowledge above.`;

    const finalResp = await this.agent.finalizer.generate(
      FINALIZER_SYSTEM,
      finalizerPrompt
    );
    totalCost += finalResp.cost;

    return new Result(finalResp.text, totalCost, pad.knowledge);
  }

  parsePlannerDecision(text) {
    if (text.includes("Action: Answer")) {
      return { action: "Answer" };
    }
    const queryMatch = text.match(/Query:\s*(.+?)(?:\n|$)/i);
    const query = queryMatch ? queryMatch[1].trim() : "what is the answer";
    return { action: "Search", query };
  }
}

module.exports = ScratchpadStrategy;
```

---

## 6. **Graph Reader Strategy (Advanced)**

```javascript
// strategies/graphReaderStrategy.js

const { Notebook, Result } = require("../types");

const PLANNER_SYSTEM = `You are a strategic planner. 
Analyze the question and break it into key elements (entities, concepts, names that need research).
Suggest 3-5 initial search queries to explore these elements.

Format:
Key Elements: [list them]
Initial Queries:
1. query1
2. query2
3. query3`;

const EXTRACTOR_SYSTEM = `You are a fact extractor.
From the given search results, extract atomic facts - single, self-contained truths.
List each fact on a new line.
Example format:
- David Baker won the Nobel Prize in Chemistry 2024
- Baker works at University of Washington
- Baker specializes in protein folding`;

const NEIGHBOR_SYSTEM = `You are a query generator.
Based on the current notebook of facts, what gaps remain to fully answer the question?
Suggest 2-3 new search queries to fill those gaps.

Format:
New Queries:
1. query1
2. query2`;

const FINALIZER_SYSTEM = `You are a research synthesizer.
Take the notebook of facts and produce a comprehensive answer.
Reference specific facts and group them logically.`;

class GraphReaderStrategy {
  constructor(agent) {
    this.agent = agent;
  }

  name() {
    return "graph-reader";
  }

  async answer(question) {
    console.log(`\n🌐 Starting Graph Reader Strategy`);
    
    const notebook = new Notebook();
    const visited = new Set();
    let queue = [];
    let totalCost = 0;
    const maxSteps = 8;

    // Step 1: Create rational plan
    console.log("\n📋 Creating rational plan...");
    const planResp = await this.agent.planner.generate(
      PLANNER_SYSTEM,
      `Question: ${question}`
    );
    totalCost += planResp.cost;
    console.log(planResp.text);

    // Extract initial queries from planner response
    const initialQueries = this.extractQueries(planResp.text);
    queue = initialQueries;
    console.log(`\n🚀 Initial queries: ${queue.join(", ")}`);

    // Step 2: Process queue
    let stepCount = 0;
    while (queue.length > 0 && stepCount < maxSteps) {
      stepCount++;
      const query = queue.shift();

      if (visited.has(query)) {
        console.log(`⏭️  Already visited: "${query}"`);
        continue;
      }
      visited.add(query);

      console.log(`\n--- Step ${stepCount} ---`);
      console.log(`🔍 Processing: "${query}"`);

      // Execute search
      const results = await this.agent.searcher.search(query);
      totalCost += (results.length * this.agent.searchCost) || 0;

      if (results.length === 0) {
        console.log("No results found");
        continue;
      }

      // Extract facts
      console.log("📚 Extracting facts...");
      const extractPrompt = `
Search Results for "${query}":
${results.map((r, i) => `${i + 1}. Title: ${r.title}\nSnippet: ${r.snippet}`).join("\n\n")}

Extract atomic facts from these results:`;

      const extractResp = await this.agent.extractor.generate(
        EXTRACTOR_SYSTEM,
        extractPrompt
      );
      totalCost += extractResp.cost;

      // Parse and add facts
      const facts = extractResp.text
        .split("\n")
        .filter((line) => line.trim().startsWith("-"))
        .map((line) => line.replace(/^-\s*/, "").trim());

      facts.forEach((fact) => {
        const url = results[0]?.url || "unknown";
        notebook.addFact(fact, url);
        console.log(`  ✓ ${fact}`);
      });

      // Step 3: Answer check
      console.log("❓ Checking if we can answer...");
      const answerCheck = await this.isAnswerable(
        question,
        notebook,
        totalCost
      );
      
      if (answerCheck.canAnswer) {
        console.log("✅ Sufficient facts gathered!");
        break;
      }

      // Step 4: Generate neighbor queries
      if (queue.length === 0) {
        console.log("🔗 Generating neighbor queries...");
        const neighborPrompt = `
Original Question: ${question}

Current Notebook:
${notebook.facts.map((f) => `- ${f.fact}`).join("\n")}

What's missing? Suggest new queries:`;

        const neighborResp = await this.agent.neighbor.generate(
          NEIGHBOR_SYSTEM,
          neighborPrompt
        );
        totalCost += neighborResp.cost;

        const newQueries = this.extractQueries(neighborResp.text);
        newQueries.forEach((q) => {
          if (!visited.has(q)) {
            queue.push(q);
          }
        });
        console.log(`  Added: ${newQueries.join(", ")}`);
      }
    }

    // Step 5: Finalize
    console.log("\n✍️  Finalizing answer...");
    const finalPrompt = `
Question: ${question}

Collected Facts:
${notebook.facts.map((f) => `- ${f.fact} (source: ${f.source})`).join("\n")}

Produce a comprehensive answer:`;

    const finalResp = await this.agent.finalizer.generate(
      FINALIZER_SYSTEM,
      finalPrompt
    );
    totalCost += finalResp.cost;

    return new Result(finalResp.text, totalCost, notebook.toJSON());
  }

  extractQueries(text) {
    const lines = text.split("\n");
    const queries = [];
    lines.forEach((line) => {
      const match = line.match(/^\d+\.\s*(.+?)(?:\n|$)/);
      if (match) {
        queries.push(match[1].trim());
      }
    });
    return queries;
  }

  async isAnswerable(question, notebook, cost) {
    // Simple heuristic: if we have at least 5 facts, we can probably answer
    return {
      canAnswer: notebook.facts.length >= 5,
      facts: notebook.facts.length,
    };
  }
}

module.exports = GraphReaderStrategy;
```

---

## 7. **Main Agent Class**

```javascript
// agent.js

const ScratchpadStrategy = require("./strategies/scratchpadStrategy");
const GraphReaderStrategy = require("./strategies/graphReaderStrategy");
const { Result } = require("./types");

class Agent {
  constructor(options = {}) {
    this.planner = options.plannerModel;
    this.synthesizer = options.synthesizerModel;
    this.finalizer = options.finalizerModel || options.synthesizerModel;
    this.extractor = options.extractorModel || options.synthesizerModel;
    this.neighbor = options.neighborModel || options.synthesizerModel;
    
    this.searcher = options.searchProvider;
    this.fetcher = options.fetchProvider;
    
    this.maxIterations = options.maxIterations || 5;
    this.searchCost = options.searchCost || 0;
    this.debug = options.debug || false;
    this.strategyName = options.strategyName || "scratchpad";
    this.priorKnowledge = "";
  }

  async answer(question, options = {}) {
    this.priorKnowledge = options.knowledge || "";

    const strategy = this.resolveStrategy();
    console.log(`\n🚀 Using strategy: ${strategy.name()}`);
    
    return await strategy.answer(question);
  }

  resolveStrategy() {
    switch (this.strategyName) {
      case "scratchpad":
        return new ScratchpadStrategy(this);
      case "graph-reader":
        return new GraphReaderStrategy(this);
      default:
        throw new Error(`Unknown strategy: ${this.strategyName}`);
    }
  }
}

module.exports = Agent;
```

---

## 8. **Complete Example Usage**

```javascript
// example.js

const Agent = require("./agent");
const { OllamaLLM, MockLLM } = require("./llmProvider");
const { DuckDuckGoSearch, MockSearch } = require("./searchProvider");
const { SearchResult } = require("./types");

/**
 * Example 1: Mock LLM + Mock Search (No API keys needed!)
 */
async function exampleMock() {
  console.log("=== Example 1: Mock Test ===\n");

  const mockSearch = new MockSearch([
    new SearchResult(
      "Why the sky is blue - Physics",
      "https://example.com/sky",
      "Rayleigh scattering causes shorter wavelengths (blue) to scatter more..."
    ),
    new SearchResult(
      "Light scattering atmosphere",
      "https://example.com/scattering",
      "The atmosphere consists of nitrogen and oxygen molecules..."
    ),
  ]);

  const agent = new Agent({
    plannerModel: new MockLLM(),
    synthesizerModel: new MockLLM(),
    finalizerModel: new MockLLM(),
    searchProvider: mockSearch,
    maxIterations: 3,
    searchCost: 0.005,
    strategyName: "scratchpad",
    debug: false,
  });

  const result = await agent.answer("Why is the sky blue?");

  console.log("\n📋 Final Result:");
  console.log("---");
  console.log("Answer:", result.answer);
  console.log(`Cost: $${result.cost.toFixed(4)}`);
  console.log("Knowledge:", result.knowledge);
}

/**
 * Example 2: Real Ollama LLM + DuckDuckGo Search
 */
async function exampleOllama() {
  console.log("=== Example 2: Ollama + DuckDuckGo ===\n");
  console.log("Make sure Ollama is running: ollama serve");
  console.log("Pull a model: ollama pull mistral\n");

  const agent = new Agent({
    plannerModel: new OllamaLLM("mistral"),
    synthesizerModel: new OllamaLLM("mistral"),
    finalizerModel: new OllamaLLM("mistral"),
    searchProvider: new DuckDuckGoSearch(),
    maxIterations: 3,
    searchCost: 0, // Local Ollama = free
    strategyName: "scratchpad",
  });

  const result = await agent.answer(
    "Who won the 2024 Nobel Prize in Chemistry?"
  );

  console.log("\n📋 Final Result:");
  console.log("---");
  console.log("Answer:", result.answer);
  console.log(`Cost: $${result.cost.toFixed(4)}`);
}

/**
 * Example 3: Graph Reader Strategy
 */
async function exampleGraphReader() {
  console.log("=== Example 3: Graph Reader Strategy ===\n");

  const agent = new Agent({
    plannerModel: new OllamaLLM("mistral"),
    extractorModel: new OllamaLLM("mistral"),
    neighborModel: new OllamaLLM("mistral"),
    finalizerModel: new OllamaLLM("mistral"),
    searchProvider: new DuckDuckGoSearch(),
    strategyName: "graph-reader",
  });

  const result = await agent.answer(
    "What are the benefits of renewable energy and which countries lead adoption?"
  );

  console.log("\n📋 Final Result:");
  console.log("---");
  console.log("Answer:", result.answer);
  console.log(`Cost: $${result.cost.toFixed(4)}`);
  console.log("Collected facts:", result.knowledge);
}

/**
 * Example 4: Follow-up Questions
 */
async function exampleFollowUp() {
  console.log("=== Example 4: Follow-up Questions ===\n");

  const agent = new Agent({
    plannerModel: new OllamaLLM("mistral"),
    synthesizerModel: new OllamaLLM("mistral"),
    finalizerModel: new OllamaLLM("mistral"),
    searchProvider: new DuckDuckGoSearch(),
    maxIterations: 3,
  });

  // First question
  console.log("Question 1: What is Tokyo's population?\n");
  const result1 = await agent.answer("What is Tokyo's population?");
  console.log("\nAnswer:", result1.answer);
  console.log(`Cost: $${result1.cost.toFixed(4)}\n`);

  // Follow-up - reuse knowledge
  console.log("\nQuestion 2: How does that compare to Osaka?\n");
  const result2 = await agent.answer(
    "How does that compare to Osaka?",
    { knowledge: result1.knowledge }
  );
  console.log("\nAnswer:", result2.answer);
  console.log(`Cost: $${result2.cost.toFixed(4)}`);
  console.log(`Total spent: $${(result1.cost + result2.cost).toFixed(4)}`);
}

// Run examples
async function main() {
  try {
    // Uncomment to run
    await exampleMock();
    // await exampleOllama();
    // await exampleGraphReader();
    // await exampleFollowUp();
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
```

---

## 9. **Setup & Installation**

```bash
# Initialize Node.js project
npm init -y

# Install dependencies (optional - using native fetch)
npm install node-fetch  # If using Node < 18

# Run examples
node example.js
```

---

## 10. **Quick Comparison: Scratchpad vs Graph Reader**

```
┌─────────────────┬──────────────────────┬──────────────────────┐
│ Aspect          │ Scratchpad           │ Graph Reader         │
├─────────────────┼──────────────────────┼──────────────────────┤
│ Complexity      │ Simple ⚡             │ Complex 🧠           │
│ Loop           │ Linear                │ Adaptive/Graph-based │
│ State           │ Text summary         │ Atomic facts + URL   │
│ LLM calls       │ ~2-4                 │ ~15-25               │
│ Cost            │ Low ($0.01-0.05)     │ High ($0.10-0.50)    │
│ Best for        │ Simple questions     │ Research questions   │
│ Context needed  │ 4k tokens            │ 16k+ tokens          │
└─────────────────┴──────────────────────┴──────────────────────┘
```

---

## 11. **Customization Examples**

### **Use Different LLM**
```javascript
// OpenAI
const { OpenAILLM } = require("./llmProvider");
const agent = new Agent({
  plannerModel: new OpenAILLM(process.env.OPENAI_API_KEY),
  synthesizerModel: new OpenAILLM(process.env.OPENAI_API_KEY),
});
```

### **Use Brave Search**
```javascript
const { BraveSearch } = require("./searchProvider");
const agent = new Agent({
  searchProvider: new BraveSearch(process.env.BRAVE_API_KEY),
});
```

### **Add Cost Tracking**
```javascript
const agent = new Agent({
  searchCost: 0.005,  // $0.005 per search
});

const result = await agent.answer("question");
console.log(`Total cost: $${result.cost.toFixed(4)}`);
```

---
