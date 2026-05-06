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

K8s and ECS tools are in-process builtin tool groups, not standalone SSE MCP
servers. Configure them under `builtin.k8s` and `builtin.ecs` in
`config/mcp_config.json`, or from the MCP management page. Process environment
variables such as `KUBECONFIG_PATH` and `ALIBABA_CLOUD_ACCESS_KEY_SECRET` still
take precedence over JSON values.

Do not commit files containing API keys, webhook tokens, cloud credentials,
kubeconfig paths, or local cluster details.
