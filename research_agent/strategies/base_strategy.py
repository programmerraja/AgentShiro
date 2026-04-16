"""Base Strategy class for Research Agent."""
from abc import ABC, abstractmethod
from research_agent.schema import Result


class Strategy(ABC):
    """Abstract base class for research strategies."""

    def __init__(self, agent):
        """
        Initialize strategy with reference to agent.

        Args:
            agent: ResearchAgent instance
        """
        self.agent = agent

    @abstractmethod
    async def answer(self, question: str) -> Result:
        """
        Answer the given question using this strategy.

        Args:
            question: The research question

        Returns:
            Result object with answer and metadata
        """
        pass

    def name(self) -> str:
        """Return strategy name."""
        return self.__class__.__name__
