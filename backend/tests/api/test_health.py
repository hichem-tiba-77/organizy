from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.main import create_app


def test_health_ok_with_real_database(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


class _BrokenSession:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_health_returns_503_when_database_is_down():
    app = create_app()
    app.dependency_overrides[get_db] = lambda: _BrokenSession()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
