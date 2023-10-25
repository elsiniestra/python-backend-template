from src.tests.conftest import clean_results


class TestGetArticles:
    @staticmethod
    def test_valid_params(client, curr_timestamp):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        assert response.json()["items"][0]["slug"].startswith("test-article")
        assert len(response.json()["items"][0]["language_variants"]) == 1
        expected = {
            "prev_page_url_params": None,
            "next_page_url_params": None,
            "items": [
                {
                    "id": 1,
                    "title": "Test Article",
                    "subtitle": "Test Subtitle",
                    "cover_image": "https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
                    "preview_image": None,
                    "tags": ["C", "B", "A"],
                    "author": "Test Test",
                    "likes": 0,
                }
            ],
            "total_items": 1,
            "total_pages": 1,
        }
        result = response.json()
        clean_results(
            result,
            expected,
            ("slug", "created_at", "language_variants"),
        )
        assert result == expected
        assert response.status_code == 200

    @staticmethod
    def test_missing_params(client):
        response = client.get("/v1/articles/?kwargs=value2")
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
    def test_valid_params_non_default_lang(client):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first", headers={"Accept-Language": "ru"})
        assert response.json()["items"][0]["slug"].startswith("test-statia")
        assert len(response.json()["items"][0]["language_variants"]) == 1
        expected = {
            "prev_page_url_params": None,
            "next_page_url_params": None,
            "items": [
                {
                    "id": 2,
                    "title": "Тест Статья",
                    "subtitle": "Тест Подзаголовок",
                    "cover_image": "https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
                    "preview_image": None,
                    "tags": ["C", "B", "A"],
                    "author": "Test Test",
                    "likes": 0,
                }
            ],
            "total_items": 1,
            "total_pages": 1,
        }
        result = response.json()
        clean_results(
            result,
            expected,
            ("slug", "created_at", "language_variants"),
        )
        assert result == expected
        assert response.status_code == 200

    @staticmethod
    def test_valid_params_main_only(client, curr_timestamp):
        response = client.get("/v1/articles/main/")
        assert response.json()["items"][0]["slug"].startswith("test-article")
        expected = {
            "items": [
                {
                    "id": 1,
                    "title": "Test Article",
                    "subtitle": "Test Subtitle",
                    "cover_image": "https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
                    "preview_image": None,
                    "tags": ["C", "B", "A"],
                    "author": "Test Test",
                    "likes": 0,
                }
            ]
        }
        result = response.json()
        clean_results(
            result,
            expected,
            ("slug", "created_at", "language_variants"),
        )
        assert result == expected
        assert response.status_code == 200


class TestGetArticlesAdmin:
    @staticmethod
    def test_valid_params(client, curr_timestamp, admin_auth_headers):
        response = client.get("/v1/admin/articles/?limit=1&page=1&offset_type=first", headers=admin_auth_headers)
        expected = {
            "items": [
                {
                    "id": 1,
                    "title": "Test Article",
                    "subtitle": "Test Subtitle",
                    "cover_image": "https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
                    "preview_image": None,
                    "tags": ["C", "B", "A"],
                    "author": "Test Test",
                    "likes": 0,
                    "is_draft": False,
                    "is_main": True,
                }
            ],
        }
        result = response.json()
        clean_results(
            result,
            expected,
            ("slug", "created_at", "language_variants"),
        )
        assert result == expected
        assert response.status_code == 200

    @staticmethod
    def test_missing_params(client):
        response = client.get("/v1/admin/articles/?kwargs=value2")
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


class TestCreateArticle:
    @staticmethod
    def test_valid_params(client, curr_timestamp, admin_auth_headers):
        article_data = {
            "title": "Test Article",
            "subtitle": "Test Subtitle",
            "cover_image": "test.jpg",
            "tags": ["tag1", "tag2"],
            "author_id": 1,
            "content": "Test content",
            "language": "en",
            "generic_id": "ab115a5a-edd3-481e-a452-6848b73d2207",
            "label": "News",
        }
        response = client.post("/v1/admin/articles/", json=article_data, headers=admin_auth_headers)
        assert response.json()["slug"].startswith("test-article")
        expected = {
            "title": "Test Article",
            "subtitle": "Test Subtitle",
            "cover_image": "test.jpg",
            "tags": ["tag1", "tag2"],
            "author_id": 1,
            "language": "en",
            "generic_id": "ab115a5a-edd3-481e-a452-6848b73d2207",
            "label": "News",
        }
        result = response.json()
        clean_results(
            result,
            expected,
            ("slug", "created_at"),
        )
        assert result == expected
        assert response.status_code == 201

        response = client.delete(f"/v1/admin/articles/{response.json()['slug']}/", headers=admin_auth_headers)
        assert response.status_code == 204

    @staticmethod
    def test_missing_params(client, admin_auth_headers):
        article_data = {
            "cover_image": "test.jpg",
            "tags": ["tag1", "tag2"],
            "author_id": 1,
            "content": "Test content",
            "language": "en",
            "label": "News",
        }
        response = client.post("/v1/admin/articles/", json=article_data, headers=admin_auth_headers)
        assert response.json() == {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["body", "title"],
                    "msg": "Field required",
                    "input": {
                        "cover_image": "test.jpg",
                        "tags": ["tag1", "tag2"],
                        "author_id": 1,
                        "content": "Test content",
                        "language": "en",
                        "label": "News",
                    },
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["body", "subtitle"],
                    "msg": "Field required",
                    "input": {
                        "cover_image": "test.jpg",
                        "tags": ["tag1", "tag2"],
                        "author_id": 1,
                        "content": "Test content",
                        "language": "en",
                        "label": "News",
                    },
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["body", "generic_id"],
                    "msg": "Field required",
                    "input": {
                        "cover_image": "test.jpg",
                        "tags": ["tag1", "tag2"],
                        "author_id": 1,
                        "content": "Test content",
                        "language": "en",
                        "label": "News",
                    },
                    "url": "https://errors.pydantic.dev/2.4/v/missing",
                },
            ]
        }
        assert response.status_code == 422

    @staticmethod
    def test_valid_params_add_new_lang():
        pass  # TODO: add case

    @staticmethod
    def test_non_eligible_author(client, user_auth_headers):
        article_data = {
            "title": "Test",
            "subtitle": "Test",
            "cover_image": "test.jpg",
            "tags": ["tag1", "tag2"],
            "author_id": 1,
            "content": "Test content",
            "language": "en",
        }
        response = client.post("/v1/admin/articles/", json=article_data, headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "detail": "User not found or have no required rights to access the endpoint.",
        }
        assert response.status_code == 422


class TestArticleRetrieve:
    @staticmethod
    def test_valid_slug(client, curr_timestamp):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        response = client.get(
            f"/v1/articles/{response.json()['items'][0]['language_variants']['ru']}/", headers={"Accept-Language": "ru"}
        )
        result = response.json()
        expected = {
            "id": 2,
            "title": "Тест Статья",
            "subtitle": "Тест Подзаголовок",
            "cover_image": "https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
            "preview_image": None,
            "tags": ["C", "B", "A"],
            "author": "Test Test",
            "content": "Тест Текст",
            "likes": 0,
        }
        clean_results(
            result,
            expected,
            ("slug", "language_variants", "created_at", "updated_at"),
        )
        assert result == expected

    @staticmethod
    def test_non_valid_slug(client):
        response = client.get("/v1/articles/vfvfvfk/")
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "ArticleNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404

    @staticmethod
    def test_draft_article_with_no_access(client, admin_auth_headers):
        response = client.get("/v1/admin/articles/?limit=2&page=1&offset_type=first", headers=admin_auth_headers)
        response = client.get(f"/v1/articles/{response.json()['items'][1]['slug']}/")
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "ArticleNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404


class TestArticleUpdate:
    @staticmethod
    def test_valid_params(client, admin_auth_headers):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        article_data = {
            "title": "Test Article2",
            "subtitle": "Test Subtitle2",
            "tags": ["A", "E", "D"],
        }
        response = client.patch(
            f"/v1/admin/articles/{response.json()['items'][0]['slug']}/", json=article_data, headers=admin_auth_headers
        )
        assert response.json()["title"] == "Test Article2"
        assert response.json()["subtitle"] == "Test Subtitle2"
        assert response.json()["tags"] == ["E", "D", "A"]
        assert response.status_code == 201
        client.patch(
            f"/v1/articles/{response.json()['slug']}/",
            json={
                "title": "Test Article",
                "subtitle": "Test Subtitle",
                "tags": ["A", "B", "C"],
            },
            headers=admin_auth_headers,
        )

    @staticmethod
    def test_missing_params(client, admin_auth_headers):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        article_data = {}
        response = client.patch(
            f"/v1/admin/articles/{response.json()['items'][0]['slug']}/", json=article_data, headers=admin_auth_headers
        )
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "UnprocessableEntityError",
            "detail": "Unprocessable Entity",
        }
        assert response.status_code == 422

    @staticmethod
    def test_invalid_slug(client, admin_auth_headers):
        article_data = {
            "title": "Test Article2",
            "subtitle": "Test Subtitle2",
        }
        response = client.patch("/v1/admin/articles/vfvfvfk/", json=article_data, headers=admin_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "ArticleNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404

    @staticmethod
    def test_not_admin(client, user_auth_headers):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        article_data = {
            "title": "Test Article2",
            "subtitle": "Test Subtitle2",
        }
        response = client.patch(
            f"/v1/admin/articles/{response.json()['items'][0]['slug']}/", json=article_data, headers=user_auth_headers
        )
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "detail": "User not found or have no required rights to access the endpoint.",
        }
        assert response.status_code == 422


class TestArticleDelete:
    @staticmethod
    def test_not_admin(client, user_auth_headers):
        response = client.get("/v1/articles/?limit=1&page=1&offset_type=first")
        response = client.delete(
            f"/v1/admin/articles/{response.json()['items'][0]['slug']}/", headers=user_auth_headers
        )
        assert response.json() == {
            "ok": False,
            "status_code": 422,
            "error": "AccessTokenProvideUserWithNoAccessRightsError",
            "detail": "User not found or have no required rights to access the endpoint.",
        }
        assert response.status_code == 422


class TestArticleLike:
    @staticmethod
    def get_article_slug(client) -> str:
        return client.get("/v1/articles/?limit=1&page=1&offset_type=first").json()["items"][0]["slug"]

    def test_valid_params(self, client, user_auth_headers):
        response = client.post(f"/v1/articles/{self.get_article_slug(client)}/like/", headers=user_auth_headers)
        assert response.json() == True
        assert response.status_code == 201

    @staticmethod
    def test_invalid_params(client, user_auth_headers):
        response = client.post("/v1/articles/test/like/", headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "ArticleNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404

    def test_no_auth(self, client):
        response = client.post(f"/v1/articles/{self.get_article_slug(client)}/like/")
        assert response.json() == {
            "ok": False,
            "status_code": 401,
            "error": "UnauthorizedAccessTokenError",
            "detail": "Access token is not provided",
        }
        assert response.status_code == 401

    def test_delete_valid_params(self, client, user_auth_headers):
        response = client.delete(f"/v1/articles/{self.get_article_slug(client)}/like/", headers=user_auth_headers)
        assert response.status_code == 204

    @staticmethod
    def test_delete_invalid_params(client, user_auth_headers):
        response = client.delete("/v1/articles/test/like/", headers=user_auth_headers)
        assert response.json() == {
            "ok": False,
            "status_code": 404,
            "error": "ArticleNotFoundError",
            "detail": "Resource Not Found",
        }
        assert response.status_code == 404

    def test_delete_no_auth(self, client):
        response = client.delete(f"/v1/articles/{self.get_article_slug(client)}/like/")
        assert response.json() == {
            "ok": False,
            "status_code": 401,
            "error": "UnauthorizedAccessTokenError",
            "detail": "Access token is not provided",
        }
        assert response.status_code == 401


# TODO: add cases
class TestArticleCommentsList:
    @staticmethod
    def test_valid_params():
        pass

    @staticmethod
    def test_invalid_comment_id():
        pass


class TestArticleCommentAnswersList:
    @staticmethod
    def test_valid_params():
        pass

    @staticmethod
    def test_invalid_comment_id():
        pass


class TestArticleCommentCreate:
    @staticmethod
    def test_valid_params():
        pass

    @staticmethod
    def test_invalid_params():
        pass

    @staticmethod
    def test_invalid_comment_id():
        pass

    @staticmethod
    def test_not_authenticated():
        pass


class TestArticleCommentUpdate:
    @staticmethod
    def test_valid_params():
        pass

    @staticmethod
    def test_invalid_params():
        pass

    @staticmethod
    def test_invalid_comment_id():
        pass

    @staticmethod
    def test_invalid_answer_id():
        pass

    @staticmethod
    def test_not_author():
        pass


class TestArticleCommentDelete:
    @staticmethod
    def test_valid_params():
        pass

    @staticmethod
    def test_invalid_comment_id():
        pass

    @staticmethod
    def test_invalid_answer_id():
        pass

    @staticmethod
    def test_not_author():
        pass


class TestArticleCommentLike:
    @staticmethod
    def test_valid_params():
        pass
