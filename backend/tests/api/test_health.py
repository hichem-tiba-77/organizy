import time
from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.db import make_engine
from app.main import create_app


def test_health_ok_with_real_database(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_fails_fast_with_503_when_database_is_unreachable():
    # Nothing listens on port 1. On Windows, libpq doesn't notice the refused
    # connection and waits for its connect timeout: without one, /health hangs.
    engine = make_engine(
        "postgresql+psycopg://organizy:organizy@127.0.0.1:1/organizy",
        connect_timeout=2,
    )

    def unreachable_db() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = unreachable_db
    started = time.monotonic()
    with TestClient(app) as client:
        response = client.get("/health")
    elapsed = time.monotonic() - started
    engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
    assert elapsed < 10
