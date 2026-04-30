from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.v2.dependencies import get_mcp_client, set_runtime_container
from src.api.v2.endpoints.mcp import get_config_manager_dep, router as mcp_router
from src.api.v2.endpoints.ops import router as ops_router
from src.app.container import RuntimeContainer
from src.security.auth import CurrentUser, get_current_user


class FakeMCPClient:
    async def list_tools(self):
        return [object(), object()]

    async def health_check(self):
        return {
            "overall_status": "connected",
            "total_tools": 2,
            "servers": {},
            "local_runtime": {
                "enabled": True,
                "status": "connected",
                "transport": "local",
                "tool_count": 2,
                "providers": [
                    {"id": "builtin-k8s", "transport": "local", "tool_count": 2, "enabled": True}
                ],
            },
            "stats": {},
        }


class FakeMCPConfigManager:
    def __init__(self):
        self.config = None
        self.saved = False

    def save_config(self):
        self.saved = True


async def fake_current_user():
    return CurrentUser(
        id="usr_test",
        username="admin",
        display_name="管理员",
        roles=["admin"],
        permissions=["*"],
    )


def test_runtime_dependency_resolves_from_app_state():
    app = FastAPI()
    client_obj = FakeMCPClient()
    container = RuntimeContainer(mcp_client=client_obj)
    app.state.container = container
    set_runtime_container(container)

    @app.get("/probe")
    async def probe(mcp_client=Depends(get_mcp_client)):
        return {"same": mcp_client is client_obj}

    response = TestClient(app).get("/probe")

    assert response.status_code == 200
    assert response.json() == {"same": True}


def test_ops_overview_uses_standard_envelope_and_runtime_data():
    app = FastAPI()
    container = RuntimeContainer(mcp_client=FakeMCPClient(), llm_processor=object())
    app.state.container = container
    set_runtime_container(container)
    app.include_router(ops_router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = fake_current_user

    response = TestClient(app).get(
        "/api/v2/ops/overview",
        headers={"X-Request-ID": "req-test-001"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["error"] is None
    assert body["meta"]["request_id"] == "req-test-001"
    assert body["meta"]["read_only"] is True
    assert body["data"]["tools"]["count"] == 2
    assert body["data"]["tools"]["transport"] == "local"
    assert body["data"]["mcpRuntime"]["transport"] == "local"
    assert body["data"]["mcpRuntime"]["status"] == "connected"
    assert body["data"]["mcpRuntime"]["tool_count"] == 2
    assert body["data"]["mcpRuntime"]["remote_connections"] == 0
    assert body["data"]["mcp_runtime"]["remote_connections"] == 0
    assert body["data"]["mcp_runtime"]["transport"] == "local"
    assert body["data"]["mcp_runtime"]["status"] == "connected"
    assert body["data"]["mcp_runtime"]["tool_count"] == 2
    assert body["data"]["mcpRuntime"]["providers"][0]["id"] == "builtin-k8s"
    assert body["data"]["mcp_runtime"]["providers"][0]["tool_count"] == 2
    assert body["data"]["system_health"]["components"]["llm"]["enabled"] is True
    assert body["data"]["topology"]["nodes"]


def test_legacy_mcp_config_update_endpoint_uses_valid_import():
    app = FastAPI()
    manager = FakeMCPConfigManager()
    app.include_router(mcp_router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_config_manager_dep] = lambda: manager

    response = TestClient(app).post(
        "/api/v2/mcp/config",
        json={
            "config": {
                "version": "1.0",
                "name": "compat-test",
                "description": "legacy compatibility test",
                "servers": [],
                "tools": [],
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "MCP配置更新成功"
    assert manager.saved is True
    assert manager.config.name == "compat-test"


def test_static_fallback_is_api_only_when_spa_missing(monkeypatch, tmp_path):
    import main

    monkeypatch.setattr(main, "static_dir", tmp_path / "static")
    monkeypatch.setattr(main, "spa_index", tmp_path / "static" / "spa" / "index.html")
    response = TestClient(main.app).get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "api_only"
    assert body["api"] == "/api/v2/status"


def test_spa_route_returns_404_when_spa_missing(monkeypatch, tmp_path):
    import main

    monkeypatch.setattr(main, "static_dir", tmp_path / "static")
    monkeypatch.setattr(main, "spa_index", tmp_path / "static" / "spa" / "index.html")
    response = TestClient(main.app).get("/spa/missing-route")

    assert response.status_code == 404
    assert response.json()["detail"] == "SPA static files are not available"
