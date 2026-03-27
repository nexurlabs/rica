# Rica - Google AI Provider (Gemini via google.genai)

import asyncio
from google import genai
from providers.base import ProviderBase


class GoogleAIProvider(ProviderBase):
    """Google AI provider using google.genai SDK (Gemini models)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)

    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:
        """Generate response using Gemini."""

        # Build contents from messages
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Config
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config["system_instruction"] = system_prompt
        if json_mode:
            config["response_mime_type"] = "application/json"

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"[GoogleAI] Generation error: {e}")

    async def validate_key(self, api_key: str) -> bool:
        """Validate API key with a minimal test call."""
        try:
            test_client = genai.Client(api_key=api_key)
            response = await test_client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents="Say 'ok'",
                config={"max_output_tokens": 5},
            )
            return bool(response.text)
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: ~4 chars per token."""
        return len(text) // 4
        
    async def get_models(self) -> list[str]:
        """Fetch list of available models for Google AI (Gemini)."""
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-pro-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ]
