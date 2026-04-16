"""Graph Reader Strategy for Research Agent."""
from research_agent.strategies.base_strategy import Strategy
from research_agent.schema import Notebook, Result
from research_agent.prompts import (
    GRAPH_PLANNER_SYSTEM,
    EXTRACTOR_SYSTEM,
    NEIGHBOR_SYSTEM,
    GRAPH_FINALIZER_SYSTEM
)
from research_agent.utils import (
    extract_queries,
    parse_facts,
    format_search_results,
    format_facts
)


class GraphReaderStrategy(Strategy):
    """Complex research strategy with fact extraction and adaptive querying."""

    async def answer(self, question: str) -> Result:
        """
        Answer a question using the graph reader strategy.

        Algorithm:
        1. Create initial plan: break question into elements, generate 3-5 queries
        2. Queue-based BFS:
           - Pop query from queue
           - Search and extract atomic facts
           - Add to notebook (with deduplication)
           - Check if answerable (heuristic: >= 5 facts)
           - Generate neighbor queries to fill gaps
           - Continue until max steps or facts sufficient
        3. Finalizer produces comprehensive answer from facts

        Args:
            question: The research question

        Returns:
            Result with answer, cost, and collected facts as JSON
        """
        print("\n🌐 Starting Graph Reader Strategy")

        notebook = Notebook()
        visited = set()
        queue = []
        total_cost = 0.0
        max_steps = 8

        # Step 1: Create rational plan
        print("\n📋 Creating rational plan...")
        plan_resp = await self.agent.llm_provider.generate(
            GRAPH_PLANNER_SYSTEM,
            f"Question: {question}"
        )
        total_cost += plan_resp.cost
        print(plan_resp.text)

        # Extract initial queries from planner response
        initial_queries = extract_queries(plan_resp.text)
        queue = initial_queries
        print(f"\n🚀 Initial queries: {', '.join(queue)}")

        # Step 2: Process queue
        step_count = 0
        while queue and step_count < max_steps:
            step_count += 1
            query = queue.pop(0)

            if query in visited:
                print(f"⏭️  Already visited: \"{query}\"")
                continue

            visited.add(query)

            print(f"\n--- Step {step_count} ---")
            print(f"🔍 Processing: \"{query}\"")

            # Execute search
            results = await self.agent.search_provider.search(query)

            if not results:
                print("No results found")
                continue

            # Extract facts
            print("📚 Extracting facts...")
            extract_prompt = f"""
Search Results for "{query}":
{format_search_results(results)}

Extract atomic facts from these results:"""

            extract_resp = await self.agent.llm_provider.generate(
                EXTRACTOR_SYSTEM,
                extract_prompt
            )
            total_cost += extract_resp.cost

            # Parse and add facts
            facts = parse_facts(extract_resp.text)
            for fact in facts:
                url = results[0].url if results else "unknown"
                notebook.add_fact(fact, url)
                print(f"  ✓ {fact}")

            # Check if answerable
            print("❓ Checking if we can answer...")
            if len(notebook.facts) >= 5:
                print("✅ Sufficient facts gathered!")
                break

            # Generate neighbor queries
            if not queue:
                print("🔗 Generating neighbor queries...")
                neighbor_prompt = f"""
Original Question: {question}

Current Notebook:
{format_facts(notebook.facts)}

What's missing? Suggest new queries:"""

                neighbor_resp = await self.agent.llm_provider.generate(
                    NEIGHBOR_SYSTEM,
                    neighbor_prompt
                )
                total_cost += neighbor_resp.cost

                new_queries = extract_queries(neighbor_resp.text)
                for q in new_queries:
                    if q not in visited:
                        queue.append(q)

                print(f"  Added: {', '.join(new_queries)}")

        # Step 3: Finalize
        print("\n✍️  Finalizing answer...")
        final_prompt = f"""
Question: {question}

Collected Facts:
{format_facts(notebook.facts)}

Produce a comprehensive answer:"""

        final_resp = await self.agent.llm_provider.generate(
            GRAPH_FINALIZER_SYSTEM,
            final_prompt
        )
        total_cost += final_resp.cost

        return Result(
            answer=final_resp.text,
            cost=total_cost,
            knowledge=notebook.to_json()
        )
