FROM node:22-bookworm-slim AS toolsearch-build

WORKDIR /build/toolsearch

COPY mcp-servers/toolsearch/package.json mcp-servers/toolsearch/package-lock.json ./
RUN npm ci

COPY mcp-servers/toolsearch/ ./
RUN npm run build && npm prune --omit=dev

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY --from=toolsearch-build /usr/local/bin/node /usr/local/bin/node

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
    && node --version

RUN pip install --no-cache-dir poetry

COPY backend-v2/pyproject.toml backend-v2/poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --without dev --no-interaction --no-ansi

COPY backend-v2/ ./

COPY --from=toolsearch-build /build/toolsearch/package.json /app/mcp-servers/toolsearch/package.json
COPY --from=toolsearch-build /build/toolsearch/dist /app/mcp-servers/toolsearch/dist
COPY --from=toolsearch-build /build/toolsearch/node_modules /app/mcp-servers/toolsearch/node_modules

RUN mkdir -p /app/data /app/logs /app/config

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
