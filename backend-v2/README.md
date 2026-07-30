# Ding Robot Backend v2

FastAPI backend for the DingTalk K8s operations assistant rewrite.

## Local Run

```bash
poetry install
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Default development login is created on first startup when no admin exists:

```text
admin / admin
```

For shared or production environments, set `APP_ENV=production`, replace
`SECRET_KEY`, restrict `CORS_ALLOW_ORIGINS`, and provide a non-default
`BOOTSTRAP_ADMIN_PASSWORD`. Production startup rejects the unsafe local defaults.
