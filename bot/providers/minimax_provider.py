# Rica - MiniMax Provider
# Supports MiniMax text models via OpenAI-compatible API and MiniMax-M3
# multimodal messages via the Anthropic-compatible API.

import httpx
from providers.base import ProviderBase
from text_sanitizer import strip_reasoning

MINIMAX_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_ANTHROPIC_URL = "https://api.minimax.io/anthropic/v1/messages"


class MiniMaxProvider(ProviderBase):
    """MiniMax provider — M2.x text models plus MiniMax-M3 multimodal."""

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
        self.api_key = api_key
        self.model = model

    async def generate(self, messages: list, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       json_mode: bool = False) -> str:
        """Generate response via MiniMax."""
        if self.model == "MiniMax-M3":
            return await self._generate_m3(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )

        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
            clean_msg = dict(msg)
            if clean_msg.get("role") == "assistant":
                clean_msg["content"] = strip_reasoning(clean_msg.get("content", ""))
            formatted.append(clean_msg)

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
                    f"{MINIMAX_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                # Better error info for common failures
                if response.status_code == 401:
                    raise RuntimeError(f"[MiniMax] 401 Unauthorized — token may have expired or lacks permissions")
                if response.status_code == 429:
                    raise RuntimeError(f"[MiniMax] Rate limited — try again shortly")
                if response.status_code >= 500:
                    raise RuntimeError(f"[MiniMax] Server error ({response.status_code}) — try again later")

                response.raise_for_status()
                data = response.json()

                if "choices" not in data or not data["choices"]:
                    raise RuntimeError(f"[MiniMax] Empty response from API: {data}")

                content = data["choices"][0]["message"]["content"]

                return strip_reasoning(content)

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"[MiniMax] HTTP {e.response.status_code}: {e.response.text[:300]}")
        except Exception as e:
            # Don't swallow the error — surface it properly
            if "[MiniMax]" in str(e):
                raise
            raise RuntimeError(f"[MiniMax] Generation error: {e}")

    async def _generate_m3(self, messages: list, system_prompt: str = "",
                           temperature: float = 0.7, max_tokens: int = 2000,
                           json_mode: bool = False) -> str:
        """Generate via MiniMax-M3's Anthropic-compatible Messages API.

        Supports text content and Anthropic-style multimodal content blocks:
        {"type": "image", "source": {"type": "base64", ...}}.
        """
        formatted = []
        for msg in messages:
            clean_msg = dict(msg)
            role = clean_msg.get("role")
            if role == "assistant":
                content = clean_msg.get("content", "")
                if isinstance(content, str):
                    clean_msg["content"] = strip_reasoning(content)
            if role in ("user", "assistant"):
                formatted.append(clean_msg)

        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    MINIMAX_ANTHROPIC_URL,
                    json=payload,
                    headers=headers,
                )
                if response.status_code == 401:
                    raise RuntimeError("[MiniMax-M3] 401 Unauthorized — token may have expired or lacks permissions")
                if response.status_code == 429:
                    raise RuntimeError("[MiniMax-M3] Rate limited — try again shortly")
                if response.status_code >= 500:
                    raise RuntimeError(f"[MiniMax-M3] Server error ({response.status_code}) — try again later")

                response.raise_for_status()
                data = response.json()
                content_blocks = data.get("content") or []
                text = "\n".join(
                    block.get("text", "")
                    for block in content_blocks
                    if block.get("type") == "text"
                ).strip()
                if not text:
                    raise RuntimeError(f"[MiniMax-M3] Empty response from API: {data}")
                return strip_reasoning(text)

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"[MiniMax-M3] HTTP {e.response.status_code}: {e.response.text[:300]}")
        except Exception as e:
            if "[MiniMax-M3]" in str(e):
                raise
            raise RuntimeError(f"[MiniMax-M3] Generation error: {e}")

    async def validate_key(self, api_key: str) -> bool:
        """Validate API key with a minimal chat completion test."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if self.model == "MiniMax-M3":
                headers["anthropic-version"] = "2023-06-01"
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                }
                url = MINIMAX_ANTHROPIC_URL
            else:
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                }
                url = f"{MINIMAX_BASE_URL}/chat/completions"
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, json=payload, headers=headers)
                return response.status_code == 200
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    async def get_models(self) -> list[str]:
        """Return known MiniMax models."""
        return [
            "MiniMax-M3",
            "MiniMax-M2.7",
            "MiniMax-M2.7-highspeed",
            "MiniMax-M2.5",
            "MiniMax-M2.5-highspeed",
            "MiniMax-M2.1",
            "MiniMax-M2.1-highspeed",
            "MiniMax-M2",
        ]
