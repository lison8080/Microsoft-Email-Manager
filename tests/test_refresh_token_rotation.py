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
    monkeypatch.setattr(main, "ACCOUNT_HEALTH_FILE", tmp_path / "account_health.json")
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
    health = json.loads((tmp_path / "account_health.json").read_text(encoding="utf-8"))
    assert access_token == "access-token"
    assert accounts["user@example.com"]["refresh_token"] == "new-refresh"
    assert accounts["user@example.com"]["client_id"] == "client-id"
    assert accounts["user@example.com"]["auth_method"] == "graph"
    assert accounts["user@example.com"]["category_key"] == "sales"
    assert accounts["user@example.com"]["tag_keys"] == ["vip"]
    assert accounts["other@example.com"]["refresh_token"] == "other-refresh"
    assert health["accounts"]["user@example.com"]["refresh_token_status"] == "healthy"
    assert health["accounts"]["user@example.com"]["refresh_token_summary"] == "Refresh token refreshed and rotated"
    assert health["accounts"]["user@example.com"]["refresh_token_checked_at"]
    assert health["accounts"]["user@example.com"]["refresh_token_rotated_at"]


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
    monkeypatch.setattr(main, "ACCOUNT_HEALTH_FILE", tmp_path / "account_health.json")
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.token_payload = {"access_token": "access-token"}

    credentials = main.AccountCredentials(
        email="user@example.com",
        refresh_token="old-refresh",
        client_id="client-id",
    )

    access_token = asyncio.run(main.get_access_token(credentials))

    accounts = read_accounts(accounts_file)
    health = json.loads((tmp_path / "account_health.json").read_text(encoding="utf-8"))
    assert access_token == "access-token"
    assert accounts["user@example.com"]["refresh_token"] == "old-refresh"
    assert health["accounts"]["user@example.com"]["refresh_token_status"] == "healthy"
    assert health["accounts"]["user@example.com"]["refresh_token_summary"] == "Refresh token checked"
    assert health["accounts"]["user@example.com"]["refresh_token_checked_at"]
    assert health["accounts"]["user@example.com"].get("refresh_token_rotated_at") is None


def test_account_list_includes_refresh_token_metadata(monkeypatch, tmp_path):
    accounts_file = tmp_path / "accounts.json"
    health_file = tmp_path / "account_health.json"
    write_accounts(
        accounts_file,
        {
            "user@example.com": {
                "refresh_token": "refresh",
                "client_id": "client-id",
            }
        },
    )
    health_file.write_text(
        json.dumps(
            {
                "accounts": {
                    "user@example.com": {
                        "status": "healthy",
                        "score": 100,
                        "summary": "OK",
                        "checked_at": "2026-05-01T01:00:00",
                        "refresh_token_status": "healthy",
                        "refresh_token_summary": "Refresh token checked",
                        "refresh_token_checked_at": "2026-05-01T02:00:00",
                        "refresh_token_rotated_at": "2026-05-01T03:00:00",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "ACCOUNTS_FILE", accounts_file)
    monkeypatch.setattr(main, "ACCOUNT_HEALTH_FILE", health_file)

    result = asyncio.run(main.get_all_accounts())

    account = result.accounts[0]
    assert account.refresh_token_status == "healthy"
    assert account.refresh_token_summary == "Refresh token checked"
    assert account.refresh_token_checked_at == "2026-05-01T02:00:00"
    assert account.refresh_token_rotated_at == "2026-05-01T03:00:00"


def test_start_refresh_token_check_reuses_running_task(monkeypatch):
    main.refresh_token_check_state.update(
        {
            "task_id": "existing-task",
            "running": True,
            "total": 1,
            "checked": 0,
            "results": {},
            "started_at": "2026-05-01T01:00:00",
            "completed_at": None,
            "error": "",
        }
    )
    called = False

    def fake_create_task(coro):
        nonlocal called
        called = True
        coro.close()

    monkeypatch.setattr(main.asyncio, "create_task", fake_create_task)

    state = main.start_refresh_token_check()

    assert state["task_id"] == "existing-task"
    assert state["running"] is True
    assert called is False
    main.refresh_token_check_state.update({"running": False})
