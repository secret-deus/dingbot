import os
from ecs_mcp.server import run


if __name__ == "__main__":
    # 允许通过环境变量开启热重载
    # export ECS_MCP_RELOAD=true
    run()


