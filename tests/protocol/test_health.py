import asyncio

from embalming_server.main import app
from httpx import ASGITransport, AsyncClient


async def _get_health() -> tuple[int, dict[str, object]]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/health")
    return response.status_code, response.json()


def test_health_reports_loaded_ruleset() -> None:
    status_code, payload = asyncio.run(_get_health())

    assert status_code == 200
    assert payload == {
        "status": "ok",
        "ruleset": "2020-06-30-project-ruling-1",
        "card_types": 13,
        "card_instances": 25,
    }
