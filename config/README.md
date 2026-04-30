# Runtime configuration

This directory is the runtime configuration root for the application.

Only `*.example.json` files should be committed. Copy the examples to their
runtime names before starting the app:

```bash
cp config/llm_config.example.json config/llm_config.json
cp config/mcp_config.example.json config/mcp_config.json
cp config/skills.example.json config/skills.json
cp config/scheduled_tasks.example.json config/scheduled_tasks.json
```

Do not commit files containing API keys, webhook tokens, cloud credentials,
kubeconfig paths, or local cluster details.
