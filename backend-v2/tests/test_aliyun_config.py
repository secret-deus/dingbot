from __future__ import annotations

import json

from app.core.config import get_settings
from app.mcp.config_store import (
    apply_mcp_updates,
    public_mcp_config,
    read_mcp_document,
    write_mcp_document,
)


def test_aliyun_public_config_masks_secret_and_preserves_scope(monkeypatch, tmp_path):
    config_path = tmp_path / "mcp_config.json"
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("ALIYUN_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIYUN_ACCESS_KEY_SECRET", raising=False)
    monkeypatch.delenv("ALIYUN_DEFAULT_REGION_ID", raising=False)

    document, _source = read_mcp_document(config_path)
    updated = apply_mcp_updates(
        document,
        {
            "aliyun": {
                "enabled": True,
                "access_key_id": "ak-test-id",
                "access_key_secret": "ak-test-secret",
                "default_region_id": "cn-shanghai",
                "allowed_regions": ["cn-shanghai", "cn-hangzhou"],
                "required_tags": {"Environment": ["prod"], "Owner": ["ops"]},
                "allowed_instance_ids": ["i-123"],
                "sls": {
                    "mappings": [
                        {
                            "service": "ding-robot",
                            "env": "prod",
                            "region_id": "cn-shanghai",
                            "project": "prod-log-project",
                            "logstore": "app-log",
                            "default_query": "level: ERROR",
                        }
                    ]
                },
            }
        },
    )
    write_mcp_document(updated, config_path)

    public = public_mcp_config(*read_mcp_document(config_path))
    serialized = json.dumps(public, ensure_ascii=False)

    assert public["aliyun"]["enabled"] is True
    assert public["aliyun"]["configured"] is True
    assert public["aliyun"]["available"] is True
    assert public["aliyun"]["default_region_id"] == "cn-shanghai"
    assert public["aliyun"]["allowed_regions"] == ["cn-shanghai", "cn-hangzhou"]
    assert public["aliyun"]["required_tags"] == {"Environment": ["prod"], "Owner": ["ops"]}
    assert public["aliyun"]["allowed_instance_ids"] == ["i-123"]
    assert public["aliyun"]["sls_mapping_count"] == 1
    assert public["aliyun"]["access_key_id_configured"] is True
    assert public["aliyun"]["access_key_secret_configured"] is True
    assert "ak-test-secret" not in serialized


def test_aliyun_empty_secret_update_does_not_clear_existing_secret(monkeypatch, tmp_path):
    config_path = tmp_path / "mcp_config.json"
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))

    document, _source = read_mcp_document(config_path)
    first = apply_mcp_updates(
        document,
        {
            "aliyun": {
                "enabled": True,
                "access_key_id": "initial-id",
                "access_key_secret": "initial-secret",
                "default_region_id": "cn-hangzhou",
            }
        },
    )
    second = apply_mcp_updates(
        first,
        {
            "aliyun": {
                "enabled": True,
                "access_key_id": "rotated-id",
                "access_key_secret": "",
                "allowed_regions": ["cn-hangzhou"],
            }
        },
    )

    aliyun = second["builtin"]["aliyun"]
    assert aliyun["access_key_id"] == "rotated-id"
    assert aliyun["access_key_secret"] == "initial-secret"
    assert aliyun["allowed_regions"] == ["cn-hangzhou"]


def test_aliyun_json_config_populates_runtime_settings(monkeypatch, tmp_path):
    config_path = tmp_path / "mcp_config.json"
    config_path.write_text(
        json.dumps(
            {
                "builtin": {
                    "aliyun": {
                        "enabled": True,
                        "access_key_id": "json-ak",
                        "access_key_secret": "json-secret",
                        "default_region_id": "cn-shenzhen",
                        "allowed_regions": ["cn-shenzhen"],
                        "required_tags": {"Environment": ["staging"]},
                        "allowed_instance_ids": ["i-json"],
                        "sls": {
                            "mappings": [
                                {
                                    "service": "api",
                                    "env": "staging",
                                    "region_id": "cn-shenzhen",
                                    "project": "api-logs",
                                    "logstore": "app",
                                }
                            ]
                        },
                    }
                },
                "servers": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("ALIYUN_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIYUN_ACCESS_KEY_SECRET", raising=False)

    settings = get_settings()

    assert settings.aliyun_mcp_enabled is True
    assert settings.aliyun_access_key_id == "json-ak"
    assert settings.aliyun_access_key_secret == "json-secret"
    assert settings.aliyun_default_region_id == "cn-shenzhen"
    assert settings.aliyun_allowed_regions == ["cn-shenzhen"]
    assert settings.aliyun_required_tags == {"Environment": ["staging"]}
    assert settings.aliyun_allowed_instance_ids == ["i-json"]
    assert settings.aliyun_sls_mappings[0]["project"] == "api-logs"
