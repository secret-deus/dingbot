from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, MessageRole, Session
from app.mcp.policy import ToolCatalogPolicy
from app.services.chat_service import ChatOrchestrator


@pytest.mark.asyncio
async def test_chat_uses_toolsearch_before_exposing_real_tools(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="toolsearch orchestration")
        session.add(chat_session)
        await session.flush()

        fake_chat = _FakeChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id, "帮我看 default pod 列表"
            )
        ]

        assert fake_chat.tool_names_by_call[0] == [
            "k8s-get-pods",
            "tool_categories",
            "tool_get",
            "toolsearch",
        ]
        assert "k8s-get-pods" in fake_chat.tool_names_by_call[1]
        assert events[-1]["type"] == "done"
        assert any(
            event["type"] == "tool_result"
            and isinstance(event["result"].get("result"), dict)
            and event["result"]["result"].get("count") == 0
            for event in events
        )

    await engine.dispose()


@pytest.mark.asyncio
async def test_chat_can_disable_tool_context_for_one_message(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-no-tools.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="no tool context")
        session.add(chat_session)
        await session.flush()

        fake_chat = _NoToolChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "只用已有上下文回答",
                tool_context_enabled=False,
            )
        ]

        assert fake_chat.tool_names_by_call == [[]]
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_discovery_only_prompt_does_not_expose_real_tools_after_toolsearch(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-discovery-only.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="discovery only")
        session.add(chat_session)
        await session.flush()

        fake_chat = _DiscoveryOnlyChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "只搜索一下 pod 相关工具，先不要执行具体 K8s 工具",
            )
        ]

        assert fake_chat.tool_names_by_call == [["tool_categories", "tool_get", "toolsearch"]]
        assert all("k8s-get-pods" not in names for names in fake_chat.tool_names_by_call)
        assert any(event["type"] == "tool_result" for event in events)
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_discovery_only_prompt_stops_after_first_toolsearch_result(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-discovery-stop.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="discovery stop")
        session.add(chat_session)
        await session.flush()

        fake_chat = _RepeatedToolSearchChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "只搜索工具：有哪些工具可以查询阿里云轻量应用服务器？先不要执行具体资源查询。",
            )
        ]

        assert len(fake_chat.tool_names_by_call) == 1
        assert [event["type"] for event in events].count("tool_result") == 1
        assert fake_chat.final_tools is None
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_aliyun_discovery_rewrites_model_ecs_category_for_swas_query(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-aliyun-discovery.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="aliyun discovery")
        session.add(chat_session)
        await session.flush()

        fake_mcp = _AliyunDiscoveryMCP()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=_MisclassifiedAliyunDiscoveryChat(),
            mcp_manager=fake_mcp,
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "只搜索工具：有哪些工具可以查询阿里云轻量应用服务器？先不要执行具体资源查询。",
            )
        ]

        assert fake_mcp.toolsearch_arguments == [
            {"query": "阿里云轻量应用服务器", "category": "aliyun", "limit": 5}
        ]
        tool_results = [event["result"] for event in events if event["type"] == "tool_result"]
        payload = json.loads(tool_results[0]["result"])
        assert payload["results"][0]["name"] == "aliyun-swas-list-instances"
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_build_messages_strips_historical_tool_calls(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-history.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="history")
        session.add(chat_session)
        await session.flush()

        orchestrator = ChatOrchestrator(db=session, chat_service=_NoToolChat(), mcp_manager=None)
        await orchestrator.message_repo.add_message(
            chat_session.id, MessageRole.USER, "查看 pod", 1
        )
        await orchestrator.message_repo.add_message(
            chat_session.id,
            MessageRole.ASSISTANT,
            "工具检索没有收敛到可执行结果",
            2,
            tool_calls=[
                {
                    "id": "call-old",
                    "type": "function",
                    "function": {"name": "toolsearch", "arguments": "{}"},
                }
            ],
        )
        await session.commit()

        messages = await orchestrator._build_messages(chat_session.id)

        assert messages == [
            {"role": "user", "content": "查看 pod"},
            {"role": "assistant", "content": "工具检索没有收敛到可执行结果"},
        ]

    await engine.dispose()


@pytest.mark.asyncio
async def test_cluster_status_intent_seeds_k8s_anchor_tools(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-k8s-anchor.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="cluster anchor tools")
        session.add(chat_session)
        await session.flush()

        fake_chat = _NoToolChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_K8SAnchorMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event async for event in orchestrator.handle_message(chat_session.id, "查看集群状态")
        ]

        first_tool_names = fake_chat.tool_names_by_call[0]
        assert "toolsearch" in first_tool_names
        assert "tool_get" in first_tool_names
        assert "tool_categories" in first_tool_names
        assert "k8s-cluster-summary" in first_tool_names
        assert "k8s-get-pods" in first_tool_names
        assert "k8s-get-deployments" in first_tool_names
        assert "k8s-get-nodes" in first_tool_names
        assert "k8s-get-events" in first_tool_names
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_mutation_intent_seeds_k8s_write_anchor_tools(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-k8s-write-anchor.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="k8s write anchor tools")
        session.add(chat_session)
        await session.flush()

        fake_chat = _NoToolChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_K8SAnchorMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "我想处理 Deployment 扩缩容，先看看当前有哪些可用能力。",
            )
        ]

        first_tool_names = fake_chat.tool_names_by_call[0]
        assert "toolsearch" in first_tool_names
        assert "k8s-scale-deployment" in first_tool_names
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_natural_scale_request_creates_pending_confirmation_without_tool_name(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-natural-scale.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="natural scale")
        session.add(chat_session)
        await session.flush()

        fake_chat = _NoToolChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_ScaleMCP(ToolCatalogPolicy(str(_scale_catalog(tmp_path)))),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "把 default 命名空间里的 Deployment confirm-demo 扩到 2 个副本",
            )
        ]

        tool_calls = [event["tool_call"] for event in events if event["type"] == "tool_call"]
        assert tool_calls == [
            {
                "id": "direct-k8s-scale-deployment",
                "type": "function",
                "function": {
                    "name": "k8s-scale-deployment",
                    "arguments": json.dumps(
                        {
                            "deployment_name": "confirm-demo",
                            "namespace": "default",
                            "replicas": 2,
                        },
                        ensure_ascii=False,
                    ),
                },
            }
        ]
        tool_results = [event["result"] for event in events if event["type"] == "tool_result"]
        assert tool_results[0]["error"] == "tool_execution_denied"
        assert tool_results[0]["requires_confirmation"] is True
        assert tool_results[0]["confirmation"]["tool"] == "k8s-scale-deployment"
        assert fake_chat.tool_names_by_call == []
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_aliyun_swas_intent_seeds_aliyun_anchor_without_k8s_service_tools(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-aliyun-anchor.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="aliyun anchor tools")
        session.add(chat_session)
        await session.flush()

        fake_chat = _NoToolChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_AliyunAnchorMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event
            async for event in orchestrator.handle_message(
                chat_session.id,
                "查询一下我阿里云轻量应用服务器实例",
            )
        ]

        first_tool_names = fake_chat.tool_names_by_call[0]
        assert "toolsearch" in first_tool_names
        assert "aliyun-swas-list-instances" in first_tool_names
        assert "k8s-get-services" not in first_tool_names
        assert "k8s-describe-service" not in first_tool_names
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_chat_returns_fallback_when_tool_fails_without_model_text(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-tool-error.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="tool error fallback")
        session.add(chat_session)
        await session.flush()

        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=_ToolErrorChat(),
            mcp_manager=_UnavailableToolMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event async for event in orchestrator.handle_message(chat_session.id, "查看集群状态")
        ]

        fallback = "".join(event.get("content", "") for event in events if event["type"] == "token")
        assert "k8s-cluster-summary 当前不可用" in fallback
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_chat_returns_k8s_unavailable_when_discovery_finds_disabled_tool(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-discovery-disabled.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="disabled discovery fallback")
        session.add(chat_session)
        await session.flush()

        fake_chat = _UnavailableDiscoveryLoopChat()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=_UnavailableDiscoveryMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event async for event in orchestrator.handle_message(chat_session.id, "查看集群状态")
        ]

        fallback = "".join(event.get("content", "") for event in events if event["type"] == "token")
        assert "当前 Kubernetes 工具不可用" in fallback
        assert "Kubernetes API 不可用" in fallback
        assert events[-1]["type"] == "done"
        assert all(event["type"] != "error" for event in events)
        assert all("k8s-cluster-summary" not in names for names in fake_chat.tool_names_by_call)
        assert any(
            event["type"] == "tool_result"
            and json.loads(event["result"]["result"])["results"][0]["available"] is False
            for event in events
        )

    await engine.dispose()


@pytest.mark.asyncio
async def test_chat_summarizes_successful_tool_results_when_model_loops(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-loop-summary.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="loop summary")
        session.add(chat_session)
        await session.flush()

        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=_ConcreteToolLoopChat(),
            mcp_manager=_ConcreteToolMCP(),
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event async for event in orchestrator.handle_message(chat_session.id, "查看集群所有pod")
        ]

        fallback = "".join(event.get("content", "") for event in events if event["type"] == "token")
        assert "重复请求相同工具" in fallback
        assert "`k8s-get-pods`: count=2" in fallback
        assert "default/web-1:Running" in fallback
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_cluster_inspection_finalizes_after_sufficient_tool_results(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-inspection.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="cluster inspection")
        session.add(chat_session)
        await session.flush()

        fake_chat = _ClusterInspectionChat()
        fake_mcp = _ClusterInspectionMCP()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=fake_mcp,
            current_user={"username": "operator", "role": "operator"},
        )

        events = [event async for event in orchestrator.handle_message(chat_session.id, "巡检集群")]

        text = "".join(event.get("content", "") for event in events if event["type"] == "token")
        assert "集群巡检报告" in text
        assert "工具结果摘要" in fake_chat.final_messages[-1]["content"]
        assert fake_chat.final_tools is None
        assert fake_mcp.called_tools == [
            "k8s-cluster-summary",
            "k8s-get-nodes",
            "k8s-get-cluster-metrics",
        ]
        assert len(fake_chat.tool_names_by_call) == 1
        assert events[-1]["type"] == "done"

    await engine.dispose()


@pytest.mark.asyncio
async def test_duplicate_tool_call_is_not_executed_again(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'chat-duplicate-tool.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        chat_session = Session(title="duplicate tool")
        session.add(chat_session)
        await session.flush()

        fake_chat = _DuplicateToolChat()
        fake_mcp = _ConcreteToolMCP()
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=fake_chat,
            mcp_manager=fake_mcp,
            current_user={"username": "operator", "role": "operator"},
        )

        events = [
            event async for event in orchestrator.handle_message(chat_session.id, "查看集群所有pod")
        ]

        text = "".join(event.get("content", "") for event in events if event["type"] == "token")
        assert "已基于第一次工具结果生成报告" in text
        assert len([event for event in events if event["type"] == "tool_result"]) == 1
        assert len(fake_chat.tool_names_by_call) == 2
        assert fake_chat.final_tools is None
        assert events[-1]["type"] == "done"

    await engine.dispose()


class _FakeChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []

    async def stream_chat(self, messages, tools=None):
        tool_names = sorted(tool["name"] for tool in (tools or []))
        self.tool_names_by_call.append(tool_names)

        call_index = len(self.tool_names_by_call)
        if call_index == 1:
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": "call-toolsearch",
                    "type": "function",
                    "function": {
                        "name": "toolsearch",
                        "arguments": json.dumps({"query": "pod 列表", "limit": 1}),
                    },
                },
            }
        elif call_index == 2:
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": "call-k8s",
                    "type": "function",
                    "function": {
                        "name": "k8s-get-pods",
                        "arguments": json.dumps({"namespace": "default"}),
                    },
                },
            }
        else:
            yield {"type": "token", "content": "default 命名空间暂无 Pod。"}
        yield {"type": "done"}


class _NoToolChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        yield {"type": "token", "content": "已按当前上下文回答。"}
        yield {"type": "done"}


class _DiscoveryOnlyChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        if len(self.tool_names_by_call) == 1:
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": "call-toolsearch",
                    "type": "function",
                    "function": {
                        "name": "toolsearch",
                        "arguments": json.dumps({"query": "pod 工具", "limit": 1}),
                    },
                },
            }
        else:
            yield {"type": "token", "content": "已找到 pod 相关候选工具。"}
        yield {"type": "done"}


class _RepeatedToolSearchChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []
        self.final_tools = "not-called"

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": f"call-toolsearch-{len(self.tool_names_by_call)}",
                "type": "function",
                "function": {
                    "name": "toolsearch",
                    "arguments": json.dumps(
                        {"query": f"轻量应用服务器 {len(self.tool_names_by_call)}", "limit": 5}
                    ),
                },
            },
        }
        yield {"type": "done"}

    async def chat(self, messages, tools=None):
        self.final_tools = tools
        return {"content": "已找到轻量应用服务器候选工具。"}


class _MisclassifiedAliyunDiscoveryChat:
    async def stream_chat(self, messages, tools=None):
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": "call-toolsearch-aliyun",
                "type": "function",
                "function": {
                    "name": "toolsearch",
                    "arguments": json.dumps(
                        {
                            "query": "阿里云轻量应用服务器",
                            "category": "ecs",
                            "limit": 5,
                        }
                    ),
                },
            },
        }
        yield {"type": "done"}

    async def chat(self, messages, tools=None):
        return {"content": "已找到轻量应用服务器候选工具。"}


class _ToolErrorChat:
    async def stream_chat(self, messages, tools=None):
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": "call-k8s-summary",
                "type": "function",
                "function": {
                    "name": "k8s-cluster-summary",
                    "arguments": "{}",
                },
            },
        }
        yield {"type": "done"}


class _ConcreteToolLoopChat:
    async def stream_chat(self, messages, tools=None):
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": "call-k8s-pods",
                "type": "function",
                "function": {
                    "name": "k8s-get-pods",
                    "arguments": json.dumps({"namespace": "all"}),
                },
            },
        }
        yield {"type": "done"}


class _ClusterInspectionChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []
        self.final_messages: list[dict] = []
        self.final_tools = "not-called"

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        for call_id, name in (
            ("call-summary", "k8s-cluster-summary"),
            ("call-nodes", "k8s-get-nodes"),
            ("call-metrics", "k8s-get-cluster-metrics"),
            ("call-pods-late", "k8s-get-pods"),
        ):
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": "{}"},
                },
            }
        yield {"type": "done"}

    async def chat(self, messages, tools=None):
        self.final_messages = messages
        self.final_tools = tools
        return {"content": "## 集群巡检报告\n\n集群当前健康。"}


class _DuplicateToolChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []
        self.final_tools = "not-called"

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": f"call-k8s-pods-{len(self.tool_names_by_call)}",
                "type": "function",
                "function": {
                    "name": "k8s-get-pods",
                    "arguments": json.dumps({"namespace": "default"}),
                },
            },
        }
        yield {"type": "done"}

    async def chat(self, messages, tools=None):
        self.final_tools = tools
        return {"content": "已基于第一次工具结果生成报告。"}


class _UnavailableDiscoveryLoopChat:
    def __init__(self):
        self.tool_names_by_call: list[list[str]] = []

    async def stream_chat(self, messages, tools=None):
        self.tool_names_by_call.append(sorted(tool["name"] for tool in (tools or [])))
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": f"call-toolsearch-{len(self.tool_names_by_call)}",
                "type": "function",
                "function": {
                    "name": "toolsearch",
                    "arguments": json.dumps({"query": "集群状态", "limit": 1}),
                },
            },
        }
        yield {"type": "done"}


class _AllowDecision:
    allowed = True
    reason = "allowed"
    requires_confirmation = False

    def to_audit_details(self, arguments):
        return {"argumentPreview": arguments}


class _UnavailableToolMCP:
    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "k8s-cluster-summary",
                "description": "集群概览",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": False,
                "unavailableReason": "未找到 kubeconfig",
            }
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        return {
            "error": "tool_unavailable",
            "reason": "kubeconfig_not_configured",
            "message": "未找到 kubeconfig",
            "tool": name,
        }


class _ConcreteToolMCP:
    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "k8s-get-pods",
                "description": "获取 Pod 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            }
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        if name == "k8s-get-pods":
            return {
                "result": {
                    "count": 2,
                    "items": [
                        {"namespace": "default", "name": "web-1", "status": "Running"},
                        {"namespace": "kube-system", "name": "coredns", "status": "Running"},
                    ],
                }
            }
        return {"error": f"unexpected tool {name}"}


class _ClusterInspectionMCP:
    def __init__(self):
        self.called_tools: list[str] = []

    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "k8s-cluster-summary",
                "description": "集群概览",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-nodes",
                "description": "获取 Node 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-cluster-metrics",
                "description": "获取集群指标",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-pods",
                "description": "获取 Pod 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        self.called_tools.append(name)
        if name == "k8s-cluster-summary":
            return {
                "result": {"nodes": 1, "pods": 10, "deployments": 4, "pod_phases": {"Running": 10}}
            }
        if name == "k8s-get-nodes":
            return {"result": {"count": 1, "items": [{"name": "minikube", "status": "Ready"}]}}
        if name == "k8s-get-cluster-metrics":
            return {
                "result": {
                    "node_count": 1,
                    "pod_count": 10,
                    "total_cpu_mcores": 185,
                    "total_memory_mib": 1250.21,
                }
            }
        if name == "k8s-get-pods":
            return {"result": {"count": 10, "items": []}}
        return {"error": f"unexpected tool {name}"}


class _UnavailableDiscoveryMCP:
    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_get",
                "description": "Get tool",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_categories",
                "description": "Tool categories",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "k8s-cluster-summary",
                "description": "集群概览",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": False,
                "unavailableReason": "Kubernetes API 不可用: connection refused",
            },
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        if name == "toolsearch":
            return {
                "result": json.dumps(
                    {
                        "query": arguments["query"],
                        "total": 1,
                        "results": [
                            {
                                "name": "k8s-cluster-summary",
                                "executionPolicy": "executable",
                                "dangerLevel": "read",
                            }
                        ],
                    }
                )
            }
        return {"error": f"unexpected tool {name}"}


class _K8SAnchorMCP:
    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_get",
                "description": "Get tool",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_categories",
                "description": "Tool categories",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "k8s-cluster-summary",
                "description": "集群概览",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-nodes",
                "description": "获取 Node 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-pods",
                "description": "获取 Pod 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-deployments",
                "description": "获取 Deployment 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-services",
                "description": "获取 Service 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-events",
                "description": "获取事件列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-get-cluster-metrics",
                "description": "获取集群指标",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "available": True,
            },
            {
                "name": "k8s-scale-deployment",
                "description": "调整 Deployment 副本数",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "replicas": {"type": "integer"},
                        "namespace": {"type": "string"},
                    },
                    "required": ["deployment_name", "replicas"],
                },
                "server": "builtin",
                "dangerLevel": "write",
                "available": True,
            },
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        return {"error": f"unexpected tool {name}"}


class _AliyunAnchorMCP:
    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_get",
                "description": "Get tool",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_categories",
                "description": "Tool categories",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "aliyun-swas-list-instances",
                "description": "查询轻量应用服务器实例列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "category": "aliyun",
                "available": True,
            },
            {
                "name": "k8s-get-services",
                "description": "获取 Service 列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "category": "kubernetes",
                "available": True,
            },
            {
                "name": "k8s-describe-service",
                "description": "获取 Service 详情",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "category": "kubernetes",
                "available": True,
            },
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        return {"error": f"unexpected tool {name}"}


class _AliyunDiscoveryMCP:
    def __init__(self):
        self.toolsearch_arguments: list[dict] = []

    async def list_tools(self, skill_id=None):
        return [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_get",
                "description": "Get tool",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_categories",
                "description": "Tool categories",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "aliyun-swas-list-instances",
                "description": "查询轻量应用服务器实例列表",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "category": "aliyun",
                "available": True,
            },
            {
                "name": "ecs-list-instances",
                "description": "列出 ECS 实例",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
                "category": "ecs",
                "available": True,
            },
        ]

    def authorize_tool_call(self, name, user, arguments=None):
        return _AllowDecision()

    async def call_tool(self, name, arguments, user=None):
        if name != "toolsearch":
            return {"error": f"unexpected tool {name}"}
        self.toolsearch_arguments.append(arguments)
        candidate_name = (
            "aliyun-swas-list-instances"
            if arguments.get("category") == "aliyun"
            else "ecs-list-instances"
        )
        return {
            "result": json.dumps(
                {
                    "query": arguments["query"],
                    "total": 1,
                    "results": [
                        {
                            "name": candidate_name,
                            "executionPolicy": "executable",
                            "dangerLevel": "read",
                        }
                    ],
                }
            )
        }


class _FakeMCP:
    def __init__(self, policy: ToolCatalogPolicy):
        self.policy = policy
        self.tools = [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_get",
                "description": "Get tool",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "tool_categories",
                "description": "Tool categories",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "k8s-get-pods",
                "description": "Get pods",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "builtin",
            },
        ]

    async def list_tools(self, skill_id=None):
        return self.tools

    def authorize_tool_call(self, name, user, arguments=None):
        return self.policy.authorize(name, user, arguments)

    async def call_tool(self, name, arguments, user=None):
        if name == "toolsearch":
            return {
                "result": json.dumps(
                    {
                        "query": arguments["query"],
                        "total": 1,
                        "results": [
                            {
                                "name": "k8s-get-pods",
                                "executionPolicy": "executable",
                                "dangerLevel": "read",
                            }
                        ],
                    }
                )
            }
        if name == "k8s-get-pods":
            return {"result": {"count": 0, "items": []}}
        return {"error": f"unexpected tool {name}"}


class _ScaleMCP:
    def __init__(self, policy: ToolCatalogPolicy):
        self.policy = policy
        self.tools = [
            {
                "name": "toolsearch",
                "description": "Search tools",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "server": "toolsearch",
            },
            {
                "name": "k8s-scale-deployment",
                "description": "调整 Deployment 副本数",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "namespace": {"type": "string"},
                        "replicas": {"type": "integer"},
                    },
                    "required": ["deployment_name", "replicas"],
                },
                "server": "builtin",
                "dangerLevel": "write",
            },
        ]

    async def list_tools(self, skill_id=None):
        return self.tools

    def authorize_tool_call(self, name, user, arguments=None):
        return self.policy.authorize(name, user, arguments)

    async def call_tool(self, name, arguments, user=None):
        return {"result": {"scaled": True}}


def _catalog(tmp_path):
    path = tmp_path / "tool_catalog.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "tools": [
                    {
                        "name": "k8s-get-pods",
                        "title": "获取 Pod 列表",
                        "category": "kubernetes",
                        "description": "获取 Kubernetes Pod 列表",
                        "tags": ["k8s", "pod"],
                        "dangerLevel": "read",
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _scale_catalog(tmp_path):
    path = tmp_path / "scale_tool_catalog.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "tools": [
                    {
                        "name": "k8s-scale-deployment",
                        "title": "调整 Deployment 副本数",
                        "category": "kubernetes",
                        "description": "调整 Kubernetes Deployment 的 replicas 副本数",
                        "tags": ["k8s", "deployment", "scale", "副本"],
                        "dangerLevel": "write",
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "deployment_name": {"type": "string"},
                                "namespace": {"type": "string"},
                                "replicas": {"type": "integer"},
                            },
                            "required": ["deployment_name", "replicas"],
                        },
                        "examples": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
