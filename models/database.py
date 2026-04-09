"""Database engine and FastAPI session dependency helpers."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/jobscraper")
engine = create_engine(DATABASE_URL)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and always close it afterward.

    FastAPI treats dependency functions with ``yield`` as setup/teardown
    dependencies. Code before ``yield`` runs before the request handler,
    and the ``finally`` block runs after the handler completes (or raises).
    This pattern gives us deterministic cleanup similar to Ruby's
    block-based resource management style.
    """

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
