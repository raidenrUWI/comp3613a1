def test_health_endpoint_returns_ok(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_users_api_returns_public_user_fields(api_client):
    response = api_client.get("/api/users")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "username": "api-student",
            "email": "api.student@example.com",
        }
    ]
