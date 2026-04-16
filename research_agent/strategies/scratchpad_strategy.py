"""Scratchpad Strategy for Research Agent."""

from research_agent.strategies.base_strategy import Strategy
from research_agent.schema import Scratchpad, Result
from research_agent.prompts import PLANNER_SYSTEM, SYNTHESIZER_SYSTEM, FINALIZER_SYSTEM
from research_agent.utils import parse_planner_decision, format_search_results


class ScratchpadStrategy(Strategy):
    """Simple iterative research strategy using a scratchpad."""

    async def answer(self, question: str) -> Result:
        """
        Answer a question using the scratchpad strategy.

        Algorithm:
        1. Loop until max iterations:
           - Planner decides if we have enough info or need to search
           - If Answer: break loop
           - If Search: execute search, synthesize results, update knowledge
        2. Finalizer produces answer from collected knowledge

        Args:
            question: The research question

        Returns:
            Result with answer, cost, and collected knowledge
        """
        pad = Scratchpad(original_question=question)
        total_cost = 0.0
        max_iterations = self.agent.max_iterations

        print(f"\n📝 Starting Scratchpad Strategy (max {max_iterations} iterations)")

        # Main loop
        for i in range(max_iterations):
            pad.iteration_count = i + 1
            print(f"\n--- Iteration {pad.iteration_count} ---")
            print(f"Scratchpad snapshot:\n{pad.snapshot()}\n")

            # Step 1: Planner decides
            print("🤔 Planner analyzing...")
            planner_resp = await self.agent.llm_provider.generate(
                PLANNER_SYSTEM, pad.snapshot()
            )
            total_cost += planner_resp.cost
            print(f"Planner response: {planner_resp.text}")

            action, query = parse_planner_decision(planner_resp.text)

            if action == "Answer":
                print("✅ Planner decided we have enough info!")
                break

            # Step 2: Search
            print(f'🔍 Searching for: "{query}"')
            search_results = await self.agent.search_provider.search(query)

            if not search_results:
                print("⚠️  No search results found")
                pad.append_history(f'Search for "{query}" returned 0 results')
                continue

            print(f"Found {len(search_results)} results")
            for idx, result in enumerate(search_results, 1):
                print(f"  {idx}. {result.title} ({result.url})")

            # Step 3: Synthesizer compresses results
            print("📚 Synthesizing results...")
            synthesis_prompt = f"""
                Current Question: {pad.original_question}

                Current Knowledge:
                {pad.knowledge or "(empty)"}

                New Search Results:
                {format_search_results(search_results)}

                Please synthesize this into a concise knowledge summary."""

            synth_resp = await self.agent.llm_provider.generate(
                SYNTHESIZER_SYSTEM, synthesis_prompt
            )
            total_cost += synth_resp.cost

            pad.knowledge = synth_resp.text
            pad.current_step = f"Last query: {query}"
            pad.append_history(f'Search & synthesize: "{query}"')

            print(f"Updated knowledge: {pad.knowledge[:100]}...")

        # Step 4: Finalizer produces answer
        print("\n✍️  Finalizer producing answer...")
        finalizer_prompt = f"""
            Question: {pad.original_question}

            Collected Knowledge:
            {pad.knowledge or "(no knowledge gathered)"}

            Please provide a clear, direct answer based on the knowledge above."""

        final_resp = await self.agent.llm_provider.generate(
            FINALIZER_SYSTEM, finalizer_prompt
        )
        total_cost += final_resp.cost

        return Result(answer=final_resp.text, cost=total_cost, knowledge=pad.knowledge)
