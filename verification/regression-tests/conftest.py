"""Keep fake scraper integration tests isolated from live service control state."""
import pytest

@pytest.fixture(autouse=True)
def isolated_fetch_coordinator(monkeypatch):
    from app.fetching import coordinator
    monkeypatch.setattr(coordinator,'guard',False)
    coordinator.cache.clear()
    yield
    coordinator.cache.clear()
