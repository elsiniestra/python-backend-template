class TestGetUsers:
    @staticmethod
    def test_valid_params(client, admin_auth_headers):
        response = client.get("/v1/admin/users/?limit=1&page=1&offset_type=first", headers=admin_auth_headers)
        assert response.json() == {
            "prev_page_url_params": None,
            "next_page_url_params": "?limit=1&offset_id=1&offset_type=next&page=2",
            "total_items": 2,
            "total_pages": 2,
            "items": [
                {"id": 1, "first_name": "Test", "last_name": "Test", "username": "testuser", "email": "user@test.com"}
            ],
        }
        assert response.status_code == 200

    @staticmethod
    def test_missing_args(client, admin_auth_headers):
        response = client.get("/v1/admin/users/?kwargs=value2", headers=admin_auth_headers)
        assert response.json() == {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["query", "limit"],
                    "msg": "Field required",
                    "input": None,
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["query", "page"],
                    "msg": "Field required",
                    "input": None,
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["query", "offset_type"],
                    "msg": "Field required",
                    "input": None,
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
            ]
        }
        assert response.status_code == 422

    @staticmethod
    def test_incorrect_access_level(client, user_auth_headers):
        response = client.get("/v1/admin/users/?limit=1&page=1&offset_type=first", headers=user_auth_headers)
        assert response.json() == {
            "detail": "User not found or have no required rights to access the endpoint.",
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "ok": False,
            "status_code": 422,
        }

        assert response.status_code == 422


class TestCreateUser:
    @staticmethod
    def test_valid_data_and_delete(client, admin_auth_headers):
        user_data = {
            "username": "New user",
            "email": "email@newmail.com",
            "first_name": "NewF",
            "last_name": "NewL",
            "password": "testpassword",
        }
        response = client.post("/v1/users/", json=user_data)
        assert response.json() == {
            "id": 3,
            "first_name": "NewF",
            "last_name": "NewL",
            "username": "new user",
            "email": "email@newmail.com",
        }
        assert response.status_code == 201

        response = client.delete("/v1/admin/users/3/", headers=admin_auth_headers)
        assert response.status_code == 204

    @staticmethod
    def test_missing_data(client, testuser, user_auth_headers):
        user_data = {"username": "New user", "email": "email@newmail.com"}
        response = client.post("/v1/users/", json=user_data, headers=user_auth_headers)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["body", "first_name"],
                    "msg": "Field required",
                    "input": {"username": "New user", "email": "email@newmail.com"},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["body", "last_name"],
                    "msg": "Field required",
                    "input": {"username": "New user", "email": "email@newmail.com"},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["body", "password"],
                    "msg": "Field required",
                    "input": {"username": "New user", "email": "email@newmail.com"},
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
            ]
        }


class TestRetrieveUser:
    @staticmethod
    def test_valid_id(client, testuser, user_auth_headers):
        response = client.get(f"/v1/users/{testuser.id}/", headers=user_auth_headers)
        assert response.json() == testuser.model_dump()
        assert response.status_code == 200

    @staticmethod
    def test_incorrect_id(client, user_auth_headers):
        response = client.get("/v1/users/1239/", headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "UserNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404

    @staticmethod
    def test_me(client, testuser, user_auth_headers):
        response = client.get("/v1/users/me/", headers=user_auth_headers)
        assert response.json() == testuser.model_dump()
        assert response.status_code == 200

    @staticmethod
    def test_me_incorrect_token(client, wrong_sub_auth_headers):
        response = client.get("/v1/users/me/", headers=wrong_sub_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideNotExistentUserError",
            "detail": "User not found. Access token was provided for not-existent user",
        }
        assert response.status_code == 422


class TestUpdateMe:
    @staticmethod
    def test_valid_params(client, testuser, user_auth_headers):
        updated_data = {"first_name": "John", "last_name": "Doe"}
        response = client.patch("/v1/users/me/", json=updated_data, headers=user_auth_headers)
        assert response.status_code == 201
        assert response.json() == {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "username": "testuser",
            "email": "user@test.com",
        }

        client.patch(
            "/v1/users/me/",
            json={"first_name": testuser.first_name, "last_name": testuser.last_name},
            headers=user_auth_headers,
        )

    @staticmethod
    def test_no_params(client, user_auth_headers):
        updated_data = {}
        response = client.patch("/v1/users/me/", json=updated_data, headers=user_auth_headers)
        assert response.status_code == 422
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "UnprocessableEntityError",
            "detail": "Unprocessable Entity",
        }


class TestDeleteUser:
    @staticmethod
    def test_incorrect_id(client, user_auth_headers):
        response = client.delete("/v1/admin/users/1239/", headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "detail": "User not found or have no required rights to access the endpoint.",
        }
        assert response.status_code == 422

    @staticmethod
    def test_incorrect_access_level(client, user_auth_headers):
        response = client.delete("/v1/admin/users/1/", headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "detail": "User not found or have no required rights to access the endpoint.",
        }
        assert response.status_code == 422


class TestAddGroupToUser:
    @staticmethod
    def test_valid_id_and_data(client, testuser, admin_auth_headers):
        group_data = {"user_group": "editor"}
        response = client.patch(
            f"/v1/admin/users/{testuser.id}/add-group/", json=group_data, headers=admin_auth_headers
        )
        assert response.json() == {"ok": True}
        assert response.status_code == 201

        response = client.patch(
            f"/v1/admin/users/{testuser.id}/remove-group/", json=group_data, headers=admin_auth_headers
        )
        assert response.json() == {"ok": True}
        assert response.status_code == 201

    @staticmethod
    def test_missing_id(client, admin_auth_headers):
        group_data = {"user_group": "randomtest"}
        response = client.patch("/v1/admin/users/add-group/", json=group_data, headers=admin_auth_headers)
        assert response.json() == {"detail": "Method Not Allowed"}
        assert response.status_code == 405

    @staticmethod
    def test_missing_group(client, testuser, admin_auth_headers):
        group_data = {"user_group": "randomtest"}
        response = client.patch(
            f"/v1/admin/users/{testuser.id}/add-group/", json=group_data, headers=admin_auth_headers
        )
        assert response.json() == {
            "detail": [
                {
                    "type": "enum",
                    "loc": ["body", "user_group"],
                    "msg": "Input should be 'superadmin' or 'editor'",
                    "input": "randomtest",
                    "ctx": {"expected": "'superadmin' or 'editor'"},
                }
            ]
        }
        assert response.status_code == 422

    @staticmethod
    def test_incorrect_access_level(client, testuser, user_auth_headers):
        group_data = {"user_group": "randomtest"}
        response = client.patch(f"/v1/admin/users/{testuser.id}/add-group/", json=group_data, headers=user_auth_headers)
        assert response.json() == {
            "detail": "User not found or have no required rights to access the endpoint.",
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "ok": False,
            "status_code": 422,
        }
        assert response.status_code == 422


class TestGetUserGroups:
    @staticmethod
    def test_valid_response(client, admin_auth_headers):
        response = client.get("/v1/admin/users/groups/", headers=admin_auth_headers)
        assert response.json() == {"data": ["superadmin", "editor"]}
        assert response.status_code == 200

    @staticmethod
    def test_incorrect_access_level(client, testuser, user_auth_headers):
        response = client.get("/v1/admin/users/groups/", headers=user_auth_headers)
        assert response.json() == {
            "detail": "User not found or have no required rights to access the endpoint.",
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "ok": False,
            "status_code": 422,
        }
        assert response.status_code == 422

    @staticmethod
    def test_valid_specific_user_response(client, admin, admin_auth_headers):
        response = client.get(f"/v1/admin/users/{admin.id}/groups/", headers=admin_auth_headers)
        assert response.json() == {"data": ["superadmin"]}
        assert response.status_code == 200

    @staticmethod
    def test_specific_user_not_found_response(client, admin_auth_headers):
        response = client.get("/v1/admin/users/1234567/groups/", headers=admin_auth_headers)
        assert response.json() == {"data": []}
        assert response.status_code == 200

    @staticmethod
    def test_specific_user_incorrect_access_level(client, testuser, user_auth_headers):
        response = client.get("/v1/admin/users/groups/", headers=user_auth_headers)
        assert response.json() == {
            "detail": "User not found or have no required rights to access the endpoint.",
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "ok": False,
            "status_code": 422,
        }
        assert response.status_code == 422
