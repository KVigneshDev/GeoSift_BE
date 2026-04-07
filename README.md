# FastAPI + Strawberry GraphQL Server

A production-grade Property Prospect Finder Built with FastAPI, Strawberry GraphQL, Beanie (MongoDB), Redis,
and BigQuery.

## Stack

| Concern | Library |
|---|---|
| Web framework | FastAPI (ASGI) |
| GraphQL | Strawberry |
| MongoDB ODM | Beanie (on Motor) |
| Auth | PyJWT + passlib[bcrypt] |
| Cache | redis-py (asyncio) |
| Data warehouse | google-cloud-bigquery |
| Config | pydantic-settings |
| Server | uvicorn |

## Project structure

```
app/
├── core/                    # Cross-cutting infrastructure
│   ├── config.py            # Env-driven settings (pydantic-settings)
│   ├── database.py          # MongoDB / Beanie bootstrap
│   ├── redis_client.py      # Redis client singleton
│   ├── bigquery_client.py   # BigQuery client singleton
│   ├── security.py          # JWT + bcrypt helpers
│   └── errors.py            # AppError / AuthError / ValidationError
│
├── context/
│   └── auth.py              # Per-request GraphQL context (user + loaders)
│
├── loaders/                 # DataLoader factories
│   ├── __init__.py
│   └── user_loader.py
│
├── services/                # Feature modules — one folder per feature
│   ├── auth/                # register / login mutations
│   ├── user/                # User + Organization models, me query
│   ├── cache/               # Redis-backed CacheService
│   └── property/            # BigQuery-backed property feature
│       ├── types.py         # Strawberry GraphQL types
│       ├── queries.py       # SQL builders
│       ├── service.py       # Business logic
│       ├── resolver.py      # GraphQL resolvers
│       ├── utils.py         # validate_bbox, to_label
│       ├── constants.py     # ⚠️  contants
│       └── mock_data.py     # ⚠️  mockData
│
├── schema.py                # Root schema — merges feature Query/Mutation classes
└── main.py                  # FastAPI app + lifespan + GraphQL router
```

## Running locally

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# then edit .env with your real values
```

Required env vars:

| Var | Description |
|---|---|
| `PORT` | HTTP port (default 4000) |
| `MONGO_URI` | MongoDB connection string |
| `SECRET_KEY` | JWT signing secret |
| `JWT_EXPIRES_HOURS` | Token expiry (default 8) |
| `REDIS_URL` | Redis connection string (default `redis://127.0.0.1:6379`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service-account JSON |
| `BIGQUERY_PROJECT_ID` | (optional) override BQ project |
| `BIGQUERY_KEY_FILE` | (optional) explicit BQ key file path |

### 3. Start the server

```bash
# Dev mode (auto-reload)
uvicorn app.main:app --reload --port 4000

# Or via the module entrypoint
python -m app.main
```

GraphQL playground: <http://localhost:4000/graphql>

## Adding a new feature

Each feature lives in its own folder under `app/services/<name>/` with a
predictable layout: `models.py` (if it has DB models), `types.py` (Strawberry
types), `service.py` (business logic), `resolver.py` (Query/Mutation classes).

To wire it into the schema, edit `app/schema.py` and add the feature's
Query and/or Mutation classes to the merge tuples:

```python
# app/schema.py
from app.services.my_feature.resolver import MyFeatureQuery, MyFeatureMutation

Query = merge_types("Query", (UserQuery, PropertyQuery, MyFeatureQuery))
Mutation = merge_types("Mutation", (AuthMutation, MyFeatureMutation))
```

## Auth

Send the JWT in the `Authorization` header.

```bash
curl -X POST http://localhost:4000/graphql \
  -H 'Content-Type: application/json' \
  -H 'Authorization: <token>' \
  -d '{"query":"{ me { id name email } }"}'
```

## Notes

- **Field naming**: Strawberry auto-converts Python `snake_case` to GraphQL
  `camelCase`, so the generated SDL works well with GraphQL clients.
- **BigQuery is sync**: The official SDK is synchronous; the property service
  wraps queries in `asyncio.to_thread` to avoid blocking the event loop.
