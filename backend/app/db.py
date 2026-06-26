"""
Capa de base de datos: engine + SessionLocal SQLAlchemy 2.x sobre SQLite.

Toda la app habla con la DB a través del Repository (repository.py); este
módulo solo expone el engine, la factory de sesiones y la Base declarativa.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()

# check_same_thread=False: FastAPI usa hilos del threadpool para endpoints sync
# y BackgroundTasks; SQLite necesita esta bandera para compartir la conexión.
_connect_args = (
    {"check_same_thread": False}
    if _settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def init_db() -> None:
    """Crea todas las tablas declaradas. Idempotente."""
    # Importar models registra las clases en la metadata de Base.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
