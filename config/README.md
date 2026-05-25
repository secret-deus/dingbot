# Runtime configuration

This directory is the runtime configuration root for the application.

Only `*.example.json` files and generated non-secret catalog artifacts should be
committed. Copy the examples to their runtime names before starting the app:

```bash
cp config/llm_config.example.json config/llm_config.json
cp config/mcp_config.example.json config/mcp_config.json
cp config/skills.example.json config/skills.json
cp config/scheduled_tasks.example.json config/scheduled_tasks.json
```

`config/tool_catalog.json` is committed because it contains ToolSearch metadata
only. Regenerate it after tool catalog changes:

```bash
cd mcp-servers/toolsearch
npm run catalog:generate
```

For local `poetry run` development, build ToolSearch before enabling the stdio
server in `mcp_config.json`:

```bash
cd mcp-servers/toolsearch
npm install
npm run build
```

For Docker Compose, the backend image builds and includes the ToolSearch runtime.
The same relative command path works from `/app` in the container:
`mcp-servers/toolsearch/dist/src/index.js`.

K8s, ECS, and Aliyun tools are in-process builtin tool groups, not standalone
SSE MCP servers. Configure them under `builtin.k8s`, `builtin.ecs`, and
`builtin.aliyun` in `config/mcp_config.json`, or from the MCP management page.
Process environment variables such as `KUBECONFIG_PATH`,
`ALIBABA_CLOUD_ACCESS_KEY_SECRET`, and `ALIYUN_ACCESS_KEY_SECRET` still take
precedence over JSON values.

The Aliyun read-only adapter exposes only the reviewed `aliyun-*` diagnostic
tools. When setting list or object fields through environment variables, use
JSON instead of comma-separated text:

```bash
ALIYUN_MCP_ENABLED=true
ALIYUN_DEFAULT_REGION_ID=cn-beijing
ALIYUN_ALLOWED_REGIONS='["cn-beijing","cn-hangzhou"]'
ALIYUN_REQUIRED_TAGS='{"env":["prod"]}'
ALIYUN_ALLOWED_INSTANCE_IDS='[]'
ALIYUN_SLS_MAPPINGS='[]'
```

Do not commit files containing API keys, webhook tokens, cloud credentials,
kubeconfig paths, or local cluster details.
