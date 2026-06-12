async def test_health_sin_auth(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["env"] == "test"
    assert "version" in data
