"""Root GraphQL schema.
this is where every feature's Query/Mutation classes are merged into the
final schema. As new features land, add their classes to the tuples below.
"""
from __future__ import annotations

import strawberry
from strawberry.tools import merge_types

from app.services.auth.resolver import AuthMutation
from app.services.property.resolver import PropertyQuery
from app.services.user.resolver import UserQuery

# --- Merge feature roots -----------------------------------------------------
# Add new feature Query classes here as they are built.
Query = merge_types("Query", (UserQuery, PropertyQuery))

# Add new feature Mutation classes here as they are built.
Mutation = merge_types("Mutation", (AuthMutation,))

schema = strawberry.Schema(query=Query, mutation=Mutation)
