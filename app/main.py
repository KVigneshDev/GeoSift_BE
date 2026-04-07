"""FastAPI application entrypoint.
Wires up:
- DB connection on startup (lifespan)
- CORS
- The Strawberry GraphQL router at `/graphql`
- A custom error formatter that returns `{ message, code }` like the Apollo
  `formatError` hook.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from graphql import GraphQLError
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from app.context.auth import GraphQLContext, get_context
from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.core.redis_client import close_redis_client
from app.schema import schema

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    yield
    await close_redis_client()
    await disconnect_db()


def _format_error(error: GraphQLError) -> dict[str, Any]:
    """Match the Apollo `formatError` shape: only message + code."""
    code: str | None = None
    if error.extensions:
        code = error.extensions.get("code")
    return {"message": error.message, "code": code}


class AppGraphQLRouter(GraphQLRouter[GraphQLContext, None]):
    """GraphQL router that strips stack traces / locations / paths from
    error responses, mirroring the original Apollo `formatError` hook."""

    async def process_result(  # type: ignore[override]
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}
        if result.errors:
            data["errors"] = [_format_error(err) for err in result.errors]
        if result.extensions:
            data["extensions"] = result.extensions
        return data


app = FastAPI(lifespan=lifespan)

# NOTE: For production, replace `allow_origins=["*"]` with an explicit list of
# trusted origins. The wildcard is incompatible with `allow_credentials=True`
# in modern browsers, so credentials are disabled here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = AppGraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
