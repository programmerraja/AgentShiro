"""LiteLLM provider for using various LLM models."""
from research_agent.providers.llm_provider import LLMProvider
from research_agent.schema import LLMResponse
from agentshiro.llm import completion


class LiteLLMProvider(LLMProvider):
    """LLM Provider using LiteLLM (supports Claude, OpenAI, Ollama, etc)."""

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", temperature: float = 0.7):
        """
        Initialize LiteLLMProvider.

        Args:
            model_name: Model to use (any litellm-supported model)
            temperature: Temperature for generation
        """
        self.model_name = model_name
        self.temperature = temperature

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Generate response using LiteLLM.

        Args:
            system_prompt: System context
            user_prompt: User input

        Returns:
            LLMResponse with text and cost tracking
        """
        try:
            response = completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                stream=False
            )

            text = response.choices[0].message.content
            cost = self._calculate_cost(response)

            return LLMResponse(text=text, cost=cost)

        except Exception as e:
            raise RuntimeError(f"LiteLLM error: {e}")

    def _calculate_cost(self, response) -> float:
        """Calculate cost from response usage."""
        try:
            usage = response.usage
            # Rough pricing estimates (will vary by model)
            # These are placeholders - actual costs depend on the model
            if "gpt-4" in self.model_name.lower():
                input_cost = (usage.prompt_tokens / 1000000) * 0.03
                output_cost = (usage.completion_tokens / 1000000) * 0.06
            elif "claude" in self.model_name.lower():
                input_cost = (usage.prompt_tokens / 1000000) * 0.003
                output_cost = (usage.completion_tokens / 1000000) * 0.015
            else:
                # Default to free (local models, etc)
                input_cost = 0
                output_cost = 0

            return input_cost + output_cost
        except Exception:
            return 0.0
