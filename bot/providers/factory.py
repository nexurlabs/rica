# Rica - Provider Factory
# Creates the right provider instance based on server config

import httpx

from providers.base import ProviderBase
from providers.google_ai import GoogleAIProvider
from providers.openrouter import OpenRouterProvider
from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.groq_provider import GroqProvider


PROVIDER_MAP = {
    "google_ai": GoogleAIProvider,
    "openrouter": OpenRouterProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "groq": GroqProvider,
}


def get_provider(provider_name: str, api_key: str, model: str = None) -> ProviderBase:
    """
    Create a provider instance.

    Args:
        provider_name: One of "google_ai", "openrouter", "openai", "anthropic"
        api_key: The decrypted API key
        model: Optional model override

    Returns:
        ProviderBase instance
    """
    provider_class = PROVIDER_MAP.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDER_MAP.keys())}")

    if model:
        return provider_class(api_key=api_key, model=model)
    return provider_class(api_key=api_key)


# Provider-specific key prefixes, ordered MOST SPECIFIC FIRST to avoid
# ambiguous matches (e.g. "sk-ant-" must be checked before "sk-").
_KEY_PREFIXES = [
    ("anthropic",   "sk-ant-"),
    ("openrouter",  "sk-or-"),
    ("groq",        "gsk_"),
    ("google_ai",   "AIza"),
    ("openai",      "sk-"),
]


def _detect_provider_mismatch(api_key: str, target_provider: str) -> str | None:
    """Check if the key obviously belongs to a DIFFERENT provider.

    Important: stop at the first matching prefix, because some providers have
    more specific prefixes that also match more general ones (e.g. anthropic
    `sk-ant-...` also starts with OpenAI's `sk-`). `_KEY_PREFIXES` is ordered
    most-specific-first for this reason.
    """
    for provider_name, prefix in _KEY_PREFIXES:
        if api_key.startswith(prefix):
            return None if provider_name == target_provider else provider_name
    return None


async def validate_provider_key(provider_name: str, api_key: str) -> bool:
    """Validate an API key for a specific provider.

    Does a quick format check first, then a live API test call.
    Raises ValueError with a user-facing reason when we can diagnose.
    """
    api_key = api_key.strip()

    # Cross-provider mismatch detection
    wrong_provider = _detect_provider_mismatch(api_key, provider_name)
    if wrong_provider:
        raise ValueError(
            f"This key looks like a {wrong_provider} key (prefix '{api_key[:8]}...'), "
            f"but you selected {provider_name} as the provider."
        )

    # Expected prefix check for the target provider
    expected = dict(_KEY_PREFIXES).get(provider_name, "")
    if expected and not api_key.startswith(expected):
        raise ValueError(
            f"Invalid key format for {provider_name}: "
            f"expected key starting with '{expected}...'"
        )

    # Live validation via provider implementation
    try:
        provider = get_provider(provider_name, api_key)
        ok = await provider.validate_key(api_key)
        if ok:
            return True

        # Provider-specific diagnostics for clearer error messages
        if provider_name == "groq":
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                if resp.status_code == 401:
                    raise ValueError("Groq rejected this key (401 invalid_api_key). Re-copy from console.groq.com and ensure no extra spaces.")
                if resp.status_code == 429:
                    raise ValueError("Groq key is valid but currently rate-limited/quota-limited (429).")
                if resp.status_code >= 500:
                    raise ValueError(f"Groq endpoint is currently failing ({resp.status_code}). Try again in a minute.")
                raise ValueError(f"Groq auth check failed (HTTP {resp.status_code}).")
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Groq validation request failed: {e}")

        raise ValueError(f"Provider authentication failed for {provider_name}.")

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Key auth failed for {provider_name}: {e}")
