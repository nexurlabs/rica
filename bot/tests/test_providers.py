# Rica Tests - Provider Factory & Key Validation

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from providers.factory import (
    get_provider,
    _detect_provider_mismatch,
    _KEY_PREFIXES,
    PROVIDER_MAP,
)
from providers.base import ProviderBase


class TestProviderFactory:
    """Tests for the provider factory."""

    def test_get_known_providers(self):
        for name in ["google_ai", "openai", "anthropic", "openrouter"]:
            provider = get_provider(name, "fake-key-12345")
            assert isinstance(provider, ProviderBase)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent", "key123")

    def test_model_override(self):
        provider = get_provider("google_ai", "AIzaFakeKey123456", model="gemini-pro")
        assert provider.model == "gemini-pro"


class TestProviderMismatchDetection:
    """Tests for cross-provider key mismatch detection."""

    def test_anthropic_key_to_openai_detected(self):
        result = _detect_provider_mismatch("sk-ant-fake123456", "openai")
        assert result == "anthropic"

    def test_openrouter_key_to_google_detected(self):
        result = _detect_provider_mismatch("sk-or-fake123456", "google_ai")
        assert result == "openrouter"

    def test_google_key_to_anthropic_detected(self):
        result = _detect_provider_mismatch("AIzaFakeKey123456", "anthropic")
        assert result == "google_ai"

    def test_correct_provider_no_mismatch(self):
        assert _detect_provider_mismatch("sk-ant-fake123456", "anthropic") is None
        assert _detect_provider_mismatch("sk-or-fake123456", "openrouter") is None
        assert _detect_provider_mismatch("AIzaFakeKey123456", "google_ai") is None

    def test_unknown_prefix_no_mismatch(self):
        assert _detect_provider_mismatch("xyz-unknown-key", "openai") is None


class TestKeyPrefixOrdering:
    """Tests that key prefix ordering is correct (most specific first)."""

    def test_anthropic_before_openai(self):
        # Ensure "sk-ant-" is checked before "sk-" in the prefix list
        anthropic_idx = None
        openai_idx = None
        for i, (name, prefix) in enumerate(_KEY_PREFIXES):
            if name == "anthropic":
                anthropic_idx = i
            if name == "openai":
                openai_idx = i
        assert anthropic_idx is not None
        assert openai_idx is not None
        assert anthropic_idx < openai_idx, "anthropic must be checked before openai"

    def test_openrouter_before_openai(self):
        or_idx = None
        oai_idx = None
        for i, (name, _) in enumerate(_KEY_PREFIXES):
            if name == "openrouter":
                or_idx = i
            if name == "openai":
                oai_idx = i
        assert or_idx < oai_idx, "openrouter must be checked before openai"

    def test_anthropic_key_not_misidentified_as_openai(self):
        """An Anthropic key starts with 'sk-ant-' which also starts with 'sk-'.
        The mismatch detector should identify it as anthropic, NOT openai."""
        result = _detect_provider_mismatch("sk-ant-api03-fake", "google_ai")
        assert result == "anthropic"  # Not "openai"
