import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_JWT_SECRET, auth_header


@pytest.fixture
def client():
    return TestClient(create_app(Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET)))


def test_projects_crud_and_cross_user_isolation(client):
    h = auth_header("owner")

    # Listing with no projects yet lazily provisions a default one.
    projects = client.get("/projects", headers=h).json()
    assert len(projects) == 1

    created = client.post("/projects", json={"name": "Brand B"}, headers=h).json()
    assert created["name"] == "Brand B"
    pid2 = created["id"]
    assert len(client.get("/projects", headers=h).json()) == 2

    # Another user can neither see nor touch this project.
    intruder = auth_header("intruder")
    assert client.get(f"/projects/{pid2}", headers=intruder).status_code == 404
    assert client.delete(f"/projects/{pid2}", headers=intruder).status_code == 404

    assert client.delete(f"/projects/{pid2}", headers=h).status_code == 200


def test_intelligence_is_scoped_per_project(client):
    h = auth_header("agency")
    p1 = client.post("/projects", json={"name": "Acme"}, headers=h).json()["id"]
    p2 = client.post("/projects", json={"name": "Globex"}, headers=h).json()["id"]

    # Assets logged to p1 are invisible from p2.
    client.post(
        "/assets",
        json={"asset_type": "ad", "project_id": p1, "metrics": {"clicks": 5}},
        headers=h,
    )
    assert len(client.get(f"/assets?project_id={p1}", headers=h).json()["assets"]) == 1
    assert client.get(f"/assets?project_id={p2}", headers=h).json()["assets"] == []

    # Voice is per-project too.
    client.post(
        "/voice/analyze",
        json={"samples": ["short. punchy. no fluff."], "project_id": p1},
        headers=h,
    )
    assert client.get(f"/voice/me?project_id={p1}", headers=h).status_code == 200
    assert client.get(f"/voice/me?project_id={p2}", headers=h).status_code == 404


def test_chat_autologs_asset_reports_metrics_and_evolves_profile(client):
    h = auth_header("founder")
    pid = client.post("/projects", json={"name": "Rocket"}, headers=h).json()["id"]

    client.post("/chat", json={"session_id": "s1", "message": "help me grow", "project_id": pid}, headers=h)
    r = client.post(
        "/chat", json={"session_id": "s1", "message": "more signups", "project_id": pid}, headers=h
    )
    assert r.json()["next_step"] == "refine"

    # (#1) The generated asset was auto-logged to the project.
    assets = client.get(f"/assets?project_id={pid}", headers=h).json()["assets"]
    assert len(assets) == 1
    assert assets[0]["asset_type"] == "email_promo"
    asset_id = assets[0]["id"]

    # (#3) The business profile evolved with the locked strategy.
    profile = client.get(f"/projects/{pid}", headers=h).json()["business_profile"]
    assert "marketing_angle" in profile

    # (#2) Results can be reported and show up in the compounding-wins summary.
    upd = client.patch(
        f"/assets/{asset_id}",
        json={"metrics": {"open_rate": "55%"}, "project_id": pid},
        headers=h,
    )
    assert upd.status_code == 200
    assert upd.json()["metrics"]["open_rate"] == "55%"
    summary = client.get(f"/assets?project_id={pid}", headers=h).json()["summary"]
    assert "open_rate=55%" in summary


class _FakeScraper:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def scrape(self, url: str) -> str:
        self.calls.append(url)
        return f"# {url}\nWe sell artisanal cold brew to remote software teams."


def test_website_in_message_is_scraped_into_context():
    scraper = _FakeScraper()
    app = create_app(
        Settings(use_fake_llm=True, jwt_secret=TEST_JWT_SECRET), scraper=scraper
    )
    c = TestClient(app)
    h = auth_header("founder")
    pid = c.post("/projects", json={"name": "Brew"}, headers=h).json()["id"]

    c.post(
        "/chat",
        json={"session_id": "s1", "message": "here's my site https://brew.example", "project_id": pid},
        headers=h,
    )
    # The URL was scraped and recorded on the project profile.
    assert scraper.calls == ["https://brew.example"]
    profile = c.get(f"/projects/{pid}", headers=h).json()["business_profile"]
    assert profile["website"] == "https://brew.example"

    # A second turn in the same session does NOT re-scrape (content is cached on state).
    c.post(
        "/chat",
        json={"session_id": "s1", "message": "what should I build?", "project_id": pid},
        headers=h,
    )
    assert scraper.calls == ["https://brew.example"]


def test_metrics_update_rejects_foreign_project(client):
    h = auth_header("u")
    pid = client.post("/projects", json={"name": "P"}, headers=h).json()["id"]
    a = client.post("/assets", json={"asset_type": "ad", "project_id": pid}, headers=h).json()
    other = client.post("/projects", json={"name": "Q"}, headers=h).json()["id"]
    # The asset belongs to pid, not other → not found under other's scope.
    r = client.patch(
        f"/assets/{a['id']}", json={"metrics": {"x": 1}, "project_id": other}, headers=h
    )
    assert r.status_code == 404
