# Rica - OpenRouter Provider
# Supports 100+ models (GPT, Claude, Gemini, Llama, Mistral, etc.)

import httpx
from providers.base import ProviderBase

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(ProviderBase):
    """OpenRouter provider — single API key, access to 100+ models."""

    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-exp:free"):
        self.api_key = api_key
        self.model = model

    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:
        """Generate response via OpenRouter API."""

        # Prepend system message
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        formatted.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://Rica-bot.com",
            "X-Title": "Rica Discord Bot",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"[OpenRouter] Generation error: {e}")

    async def validate_key(self, api_key: str) -> bool:
        """Validate API key against an auth-protected endpoint."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://Rica-bot.com",
                "X-Title": "Rica Discord Bot",
            }
            async with httpx.AsyncClient(timeout=10) as client:
                # NOTE: /models is publicly accessible on OpenRouter and cannot validate keys.
                response = await client.get(
                    f"{OPENROUTER_BASE_URL}/auth/key",
                    headers=headers,
                )
                if response.status_code != 200:
                    return False
                data = response.json()
                return bool(data.get("data")) if isinstance(data, dict) else True
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
        
    async def get_models(self) -> list[str]:
        """Fetch list of available models from OpenRouter."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{OPENROUTER_BASE_URL}/models")
                if response.status_code == 200:
                    data = response.json()
                    return [model["id"] for model in data.get("data", [])]
                return []
        except Exception:
            return []
