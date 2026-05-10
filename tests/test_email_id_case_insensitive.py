import asyncio
import json

import main


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_account_credentials_resolves_email_id_case_insensitively(monkeypatch, tmp_path):
    accounts_file = tmp_path / "accounts.json"
    write_json(
        accounts_file,
        {
            "User.Name@Outlook.com": {
                "refresh_token": "refresh-token",
                "client_id": "client-id",
            }
        },
    )
    monkeypatch.setattr(main, "ACCOUNTS_FILE", accounts_file)

    credentials = asyncio.run(main.get_account_credentials("user.name@outlook.com"))

    assert str(credentials.email).casefold() == "user.name@outlook.com"
    assert credentials.refresh_token == "refresh-token"


def test_public_share_meta_resolves_email_id_case_insensitively(monkeypatch, tmp_path):
    shares_file = tmp_path / "public_shares.json"
    write_json(
        shares_file,
        {
            "shares": {
                "User.Name@Outlook.com": {
                    "enabled": True,
                    "expires_at": None,
                }
            }
        },
    )
    monkeypatch.setattr(main, "PUBLIC_SHARES_FILE", shares_file)

    meta = main.get_public_share_meta("user.name@outlook.com")

    assert meta["enabled"] is True


def test_email_tags_reuse_existing_email_key_case_insensitively(monkeypatch, tmp_path):
    tags_file = tmp_path / "email_tags.json"
    write_json(
        tags_file,
        {
            "emails": {
                "User.Name@Outlook.com": {
                    "message-1": ["registered"],
                }
            }
        },
    )
    monkeypatch.setattr(main, "EMAIL_TAGS_FILE", tags_file)

    main.set_email_tag_keys("user.name@outlook.com", "message-2", ["vip"])

    tags = read_json(tags_file)["emails"]
    assert list(tags.keys()) == ["User.Name@Outlook.com"]
    assert tags["User.Name@Outlook.com"]["message-1"] == ["registered"]
    assert tags["User.Name@Outlook.com"]["message-2"] == ["vip"]


def test_clear_email_cache_matches_email_id_case_insensitively():
    main.email_cache.clear()
    main.email_count_cache.clear()
    main.email_cache["User.Name@Outlook.com:imap:inbox:1:20"] = ("cached", 0)

    main.clear_email_cache("user.name@outlook.com")

    assert main.email_cache == {}
