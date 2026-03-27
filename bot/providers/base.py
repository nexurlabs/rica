# Rica - Provider Base Class
# Unified interface for all AI providers (BYOK)

from abc import ABC, abstractmethod


class ProviderBase(ABC):
    """Base class for all AI providers."""

    @abstractmethod
    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:
        """
        Generate a response from the AI model.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Max output tokens
            json_mode: If True, force JSON output

        Returns:
            Response text string
        """
        pass

    @abstractmethod
    async def validate_key(self, api_key: str) -> bool:
        """Test if an API key is valid by making a minimal API call."""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of tokens for usage tracking."""
        pass
        
    @abstractmethod
    async def get_models(self) -> list[str]:
        """Fetch list of available models for this provider."""
        pass
