"""LLM stream fallback behavior tests."""

import asyncio

from src.llm.processor import EnhancedLLMProcessor


def test_stream_chat_without_llm_client_uses_fallback_response():
    processor = EnhancedLLMProcessor(
        {
            "enabled": True,
            "provider": "openai",
            "model": "test-model",
            "api_key": "test-key",
        }
    )
    processor.client = None

    async def collect_stream():
        chunks = []
        async for chunk in processor.stream_chat("hello", enable_tools=True):
            chunks.append(chunk)
        return "".join(chunks)

    response = asyncio.run(collect_stream())

    assert "LLM服务未正确配置" in response
