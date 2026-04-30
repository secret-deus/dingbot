"""LLM stream fallback behavior tests."""

import asyncio
from types import SimpleNamespace

from src.llm.processor import EnhancedLLMProcessor


class _FakeCompletions:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class _FakeClient:
    def __init__(self, response):
        self.completions = _FakeCompletions(response)
        self.chat = SimpleNamespace(completions=self.completions)


def _completion_response(content):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class _FakeStream:
    def __init__(self, parts):
        self.parts = list(parts)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.parts:
            raise StopAsyncIteration
        content = self.parts.pop(0)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=content),
                )
            ]
        )


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


def test_tool_response_prompt_compacts_hyphenated_k8s_results():
    processor = EnhancedLLMProcessor(
        {
            "enabled": True,
            "provider": "openai",
            "model": "test-model",
            "api_key": "test-key",
            "base_url": "http://127.0.0.1:9",
            "timeout": 1,
            "max_retries": 0,
        }
    )
    processor.MAX_RESULT_SIZE = 100
    processor.SUMMARY_TARGET_SIZE = 300

    result = {
        "status": "success",
        "message": "集群摘要",
        "data": {
            "nodes": [
                {"name": f"node-{i}", "status": "Ready", "cpu": f"{i}%"}
                for i in range(80)
            ],
            "recommendations": ["enable-intelligent-analysis"] * 20,
        },
    }

    prompt = processor._get_tool_response_user_prompt(
        "查看集群资源占用",
        [{"name": "k8s-cluster-summary", "arguments": "{}"}],
        [result],
    )

    assert "k8s-cluster-summary" in prompt
    assert "工具结果已压缩" in prompt
    assert len(prompt) < 2500


def test_openai_client_uses_configured_max_retries():
    processor = EnhancedLLMProcessor(
        {
            "enabled": True,
            "provider": "openai",
            "model": "test-model",
            "api_key": "test-key",
            "base_url": "http://127.0.0.1:9",
            "timeout": 1,
            "max_retries": 0,
        }
    )

    assert processor.client.max_retries == 0


def test_phase_two_non_stream_preserves_configured_max_tokens():
    processor = EnhancedLLMProcessor(
        {
            "enabled": True,
            "provider": "openai",
            "model": "test-model",
            "api_key": "test-key",
            "base_url": "http://127.0.0.1:9",
            "timeout": 1,
            "max_retries": 0,
            "max_tokens": 2400,
            "stream": False,
        }
    )
    fake_client = _FakeClient(_completion_response("ok"))
    processor.client = fake_client

    async def collect_response():
        chunks = []
        async for chunk in processor._phase_two_generate_response(
            "查看集群资源占用",
            [{"name": "k8s-cluster-summary", "arguments": "{}"}],
            [{"status": "success", "data": {"cpu": "low"}}],
        ):
            chunks.append(chunk)
        return "".join(chunks)

    response = asyncio.run(collect_response())

    assert response == "ok"
    assert fake_client.completions.calls[0]["max_tokens"] == 2400
    assert fake_client.completions.calls[0]["stream"] is False


def test_phase_two_stream_consumes_response_under_timeout():
    processor = EnhancedLLMProcessor(
        {
            "enabled": True,
            "provider": "openai",
            "model": "test-model",
            "api_key": "test-key",
            "base_url": "http://127.0.0.1:9",
            "timeout": 1,
            "max_retries": 0,
            "max_tokens": 2200,
            "stream": True,
        }
    )
    fake_client = _FakeClient(_FakeStream(["stream", " ok"]))
    processor.client = fake_client

    async def collect_response():
        chunks = []
        async for chunk in processor._phase_two_generate_response(
            "查看集群资源占用",
            [{"name": "k8s-get-cluster-metrics", "arguments": "{}"}],
            [{"status": "success", "data": {"cpu": "low"}}],
        ):
            chunks.append(chunk)
        return "".join(chunks)

    response = asyncio.run(collect_response())

    assert response == "stream ok"
    assert fake_client.completions.calls[0]["max_tokens"] == 2200
    assert fake_client.completions.calls[0]["stream"] is True
