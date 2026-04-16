"""Example usage of the Research Agent."""

import asyncio
from research_agent import (
    ResearchAgent,
    SearchResult,
    MockSearch,
    MockLLM,
)


async def example_mock():
    """Example 1: Mock LLM + Mock Search (no API calls, fast testing)."""
    print("=== Example 1: Mock Test ===\n")

    # Create mock search results
    mock_results = [
        SearchResult(
            title="Why the sky is blue - Physics",
            url="https://example.com/sky",
            snippet="Rayleigh scattering causes shorter wavelengths (blue) to scatter more than longer wavelengths (red) in the atmosphere.",
        ),
        SearchResult(
            title="Light scattering in atmosphere",
            url="https://example.com/scattering",
            snippet="The atmosphere consists of nitrogen and oxygen molecules that scatter sunlight.",
        ),
    ]

    agent = ResearchAgent(
        model_name="mock",
        strategy="scratchpad",
        llm_provider=MockLLM(),
        search_provider=MockSearch(mock_results=mock_results),
        max_iterations=3,
    )

    result = await agent.answer("Why is the sky blue?")

    print("\n📋 Final Result:")
    print("---")
    print(f"Answer: {result.answer}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Knowledge: {result.knowledge}\n")


async def example_real():
    """Example 2: Real LLM (Claude) + DuckDuckGo Search."""
    print("=== Example 2: Real Agent (Claude + DuckDuckGo) ===\n")

    agent = ResearchAgent(
        model_name="nvidia_nim/qwen/qwen3-next-80b-a3b-instruct",
        strategy="scratchpad",
        max_iterations=3,
    )

    result = await agent.answer("Who won the 2024 Nobel Prize in Chemistry?")

    print("\n📋 Final Result:")
    print("---")
    print(f"Answer: {result.answer}")
    print(f"Cost: ${result.cost:.4f}\n")


async def example_graph_reader():
    """Example 3: Graph Reader Strategy with real providers."""
    print("=== Example 3: Graph Reader Strategy ===\n")

    agent = ResearchAgent(
        model_name="claude-3-5-sonnet-20241022",
        strategy="graph-reader",
        max_iterations=8,
    )

    result = await agent.answer(
        "What are the main benefits of renewable energy and which countries lead in adoption?"
    )

    print("\n📋 Final Result:")
    print("---")
    print(f"Answer: {result.answer}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Facts collected: {result.knowledge}\n")


async def example_follow_up():
    """Example 4: Follow-up questions with knowledge reuse."""
    print("=== Example 4: Follow-up Questions ===\n")

    agent = ResearchAgent(
        model_name="claude-3-5-sonnet-20241022", strategy="scratchpad", max_iterations=3
    )

    # First question
    print("Question 1: What is Tokyo's population?\n")
    result1 = await agent.answer("What is Tokyo's population?")
    print(f"\nAnswer: {result1.answer}")
    print(f"Cost: ${result1.cost:.4f}\n")

    # Follow-up - could reuse knowledge
    print("\nQuestion 2: How does that compare to Osaka?\n")
    result2 = await agent.answer(
        "How does that compare to Osaka?", knowledge=result1.knowledge
    )
    print(f"\nAnswer: {result2.answer}")
    print(f"Cost: ${result2.cost:.4f}")
    print(f"Total spent: ${(result1.cost + result2.cost):.4f}\n")


async def main():
    """Run examples."""
    try:
        # Uncomment to run different examples
        # await example_mock()
        await example_real()  # Requires ANTHROPIC_API_KEY
        # await example_graph_reader()
        # await example_follow_up()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
