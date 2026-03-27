# Rica - OpenAI Provider

import httpx
from providers.base import ProviderBase

OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider(ProviderBase):
    """OpenAI provider (GPT-4, GPT-3.5, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:

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
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"[OpenAI] Generation error: {e}")

    async def validate_key(self, api_key: str) -> bool:
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{OPENAI_BASE_URL}/models",
                    headers=headers,
                )
                return response.status_code == 200
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
        
    async def get_models(self) -> list[str]:
        """Fetch list of available models from OpenAI."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{OPENAI_BASE_URL}/models",
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    return [model["id"] for model in data.get("data", []) if "gpt" in model["id"] or "o1" in model["id"] or "o3" in model["id"]]
                return ["gpt-4o", "gpt-4o-mini"]
        except Exception:
            return ["gpt-4o", "gpt-4o-mini"]
