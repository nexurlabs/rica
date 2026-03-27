# Rica - Groq Provider

import httpx
from providers.base import ProviderBase

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(ProviderBase):
    """Groq API provider (Llama 3, Mixtral, etc.). Uses OpenAI compatibility layer."""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
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
                    f"{GROQ_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if response.status_code != 200:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"[Groq] Generation error: {str(e)}")

    async def validate_key(self, api_key: str) -> bool:
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{GROQ_BASE_URL}/models",
                    headers=headers,
                )
                return response.status_code == 200
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
        
    async def get_models(self) -> list[str]:
        """Fetch list of available models from Groq."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{GROQ_BASE_URL}/models",
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    # Filter out models that are exclusively for audio translation/transcription 
                    # since they cause 400 Bad Request on the chat completions endpoint.
                    return [model["id"] for model in data.get("data", []) if "whisper" not in model["id"].lower()]
                return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
        except Exception:
            return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
