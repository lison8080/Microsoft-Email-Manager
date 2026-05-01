import asyncio
import json

import main


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.is_success = True
        self.status_code = 200

    def json(self):
        return self._payload


class FakeAsyncClient:
    token_payload = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, token_url, data):
        return FakeResponse(self.token_payload)


def write_accounts(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def read_accounts(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_access_token_persists_rotated_refresh_token(monkeypatch, tmp_path):
    accounts_file = tmp_path / "accounts.json"
    write_accounts(
        accounts_file,
        {
            "user@example.com": {
                "refresh_token": "old-refresh",
                "client_id": "client-id",
                "auth_method": "graph",
                "category_key": "sales",
                "tag_keys": ["vip"],
            },
            "other@example.com": {
                "refresh_token": "other-refresh",
                "client_id": "other-client",
            },
        },
    )
    monkeypatch.setattr(main, "ACCOUNTS_FILE", accounts_file)
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.token_payload = {
        "access_token": "access-token",
        "refresh_token": "new-refresh",
    }

    credentials = main.AccountCredentials(
        email="user@example.com",
        refresh_token="old-refresh",
        client_id="client-id",
        auth_method="graph",
    )

    access_token = asyncio.run(main.get_access_token(credentials))

    accounts = read_accounts(accounts_file)
    assert access_token == "access-token"
    assert accounts["user@example.com"]["refresh_token"] == "new-refresh"
    assert accounts["user@example.com"]["client_id"] == "client-id"
    assert accounts["user@example.com"]["auth_method"] == "graph"
    assert accounts["user@example.com"]["category_key"] == "sales"
    assert accounts["user@example.com"]["tag_keys"] == ["vip"]
    assert accounts["other@example.com"]["refresh_token"] == "other-refresh"


def test_get_access_token_leaves_refresh_token_when_response_omits_it(monkeypatch, tmp_path):
    accounts_file = tmp_path / "accounts.json"
    write_accounts(
        accounts_file,
        {
            "user@example.com": {
                "refresh_token": "old-refresh",
                "client_id": "client-id",
            }
        },
    )
    monkeypatch.setattr(main, "ACCOUNTS_FILE", accounts_file)
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.token_payload = {"access_token": "access-token"}

    credentials = main.AccountCredentials(
        email="user@example.com",
        refresh_token="old-refresh",
        client_id="client-id",
    )

    access_token = asyncio.run(main.get_access_token(credentials))

    accounts = read_accounts(accounts_file)
    assert access_token == "access-token"
    assert accounts["user@example.com"]["refresh_token"] == "old-refresh"
