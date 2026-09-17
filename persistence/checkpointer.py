from functools import lru_cache

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from config.settings import settings


@lru_cache(maxsize=1)
def get_postgres_pool():

    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    return ConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=1,
        max_size=10,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        },
        open=True,
    )


@lru_cache(maxsize=1)
def get_checkpointer():

    pool = get_postgres_pool()

    return PostgresSaver(pool)
