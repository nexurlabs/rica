# Rica - Anthropic Provider

import httpx
from providers.base import ProviderBase

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"


class AnthropicProvider(ProviderBase):
    """Anthropic provider (Claude models)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:

        # Anthropic uses a different format — system is separate
        formatted = []
        for msg in messages:
            formatted.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{ANTHROPIC_BASE_URL}/messages",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                # Anthropic returns content as list of blocks
                content_blocks = data.get("content", [])
                return "".join(
                    block.get("text", "") for block in content_blocks
                    if block.get("type") == "text"
                )
        except Exception as e:
            raise RuntimeError(f"[Anthropic] Generation error: {e}")

    async def validate_key(self, api_key: str) -> bool:
        try:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": "Say ok"}],
                "max_tokens": 5,
            }
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{ANTHROPIC_BASE_URL}/messages",
                    json=payload,
                    headers=headers,
                )
                return response.status_code == 200
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
        
    async def get_models(self) -> list[str]:
        """Fetch list of available models for Anthropic."""
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ]
