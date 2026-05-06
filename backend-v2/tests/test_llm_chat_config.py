from __future__ import annotations

from app.llm.chat import ChatService
from app.llm.config_store import LLMProviderRuntime


def test_openai_compatible_base_url_uses_litellm_provider_prefix():
    service = ChatService(
        LLMProviderRuntime(
            id="openai",
            name="OPENAI",
            enabled=True,
            model="MiMo-V2.5",
            api_key="secret",
            base_url="https://example.test/v1/",
            temperature=0.3,
            max_tokens=2000,
            timeout=30,
            stream=False,
        )
    )

    assert service._build_kwargs()["model"] == "openai/MiMo-V2.5"


def test_prefixed_model_is_not_prefixed_again():
    service = ChatService(
        LLMProviderRuntime(
            id="openai",
            name="OPENAI",
            enabled=True,
            model="openai/gpt-4o-mini",
            api_key="secret",
            base_url="https://api.openai.com/v1",
            temperature=0.3,
            max_tokens=2000,
            timeout=30,
            stream=True,
        )
    )

    assert service._build_kwargs()["model"] == "openai/gpt-4o-mini"
