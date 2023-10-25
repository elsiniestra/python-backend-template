from fastapi.testclient import TestClient


def test_rotate_token_success(client: TestClient):
    payload = {"username": "testuser", "password": "testpassword"}
    response = client.post("/v1/oauth/rotate-token/", json=payload)
    assert response.status_code == 201
    assert "refresh_token" in response.json()
    assert "access_token" in response.json()


def test_rotate_token_missing_fields(client: TestClient):
    payload = {"username": "testuser"}
    response = client.post("/v1/oauth/rotate-token/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()
    assert len(response.json()["detail"]) == 1
    assert response.json()["detail"][0]["loc"] == ["body", "password"]
    assert response.json()["detail"][0]["msg"] == "Field required"
    assert response.json()["detail"][0]["type"] == "missing"


async def test_refresh_token_success(client: TestClient, testuser, user_tokens, redis_pipe):
    async with redis_pipe:
        await redis_pipe.sadd(testuser.id, user_tokens.refresh_token).execute()
    headers = {"Authorization": f"Bearer {user_tokens.refresh_token}"}
    response = client.post("/v1/oauth/refresh-token/", headers=headers)
    assert response.status_code == 201
    assert "refresh_token" in response.json()
    assert "access_token" in response.json()


async def test_refresh_token_valid_but_not_in_redis(client: TestClient, testuser, user_tokens, redis_pipe):
    async with redis_pipe:
        await redis_pipe.srem(testuser.id, user_tokens.refresh_token).execute()
        headers = {"Authorization": f"Bearer {user_tokens.refresh_token}"}
        response = client.post("/v1/oauth/refresh-token/", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Could not validate credentials. Incorrect token or token payload"
        await redis_pipe.sadd(testuser.id, user_tokens.refresh_token).execute()


def test_refresh_token_missing_token(client: TestClient):
    headers = {"Authorization": "Bearer"}
    response = client.post("/v1/oauth/refresh-token/", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is not provided or not valid"


def test_refresh_or_access_token_expired(client: TestClient, expired_auth_headers):
    response = client.post("/v1/oauth/refresh-token/", headers=expired_auth_headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is not provided or not valid"


def test_refresh_or_access_token_wrong_sub(client: TestClient, wrong_sub_auth_headers):
    response = client.post("/v1/oauth/refresh-token/", headers=wrong_sub_auth_headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is not provided or not valid"


def test_refresh_token_using_access(client: TestClient, user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens.access_token}"}
    response = client.post("/v1/oauth/refresh-token/", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is not provided or not valid"
