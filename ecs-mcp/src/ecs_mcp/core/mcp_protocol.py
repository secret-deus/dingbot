"""
MCP协议类型（ECS MCP）
"""

import json
import uuid
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class MCPErrorCode(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    TOOL_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002


class MCPToolSchema(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    input_schema: Dict[str, Any] = Field(...)
    timeout: Optional[int] = Field(None, description="工具执行超时时间（秒）")
    category: Optional[str] = Field(None, description="工具分类")


class MCPCallToolResult(BaseModel):
    content: List[Dict[str, Any]] = Field(...)
    is_error: bool = Field(default=False)

    @classmethod
    def success(cls, content: Union[str, Dict[str, Any]]):
        if isinstance(content, str):
            return cls(content=[{"type": "text", "text": content}])
        return cls(content=[{"type": "text", "text": json.dumps(content, ensure_ascii=False, indent=2)}])

    @classmethod
    def error(cls, message: str, details: Any = None):
        error_content = {"error": message}
        if details is not None:
            error_content["details"] = details
        return cls(content=[{"type": "text", "text": json.dumps(error_content, ensure_ascii=False, indent=2)}], is_error=True)


def generate_request_id() -> str:
    return str(uuid.uuid4())





