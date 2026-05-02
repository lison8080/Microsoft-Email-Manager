import json
import subprocess
from pathlib import Path


def _parse_batch_line(line: str, auth_method: str) -> dict:
    html = Path("static/index.html").read_text(encoding="utf-8")
    start = html.index("function parseBatchAccountLine")
    end = html.index("function updateAddAccountMethodHints", start)
    script = (
        html[start:end]
        + "\n"
        + "const parsed = parseBatchAccountLine(process.argv[1], process.argv[2]);\n"
        + "process.stdout.write(JSON.stringify(parsed));\n"
    )
    result = subprocess.run(
        ["node", "-e", script, line, auth_method],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_imap_default_detects_graph_four_column_batch_format():
    client_id = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"
    refresh_token = "M.C561_BAY.0.U.-example-refresh-token"
    parsed = _parse_batch_line(
        f"user@outlook.com----password----{client_id}----{refresh_token}",
        "imap",
    )

    assert parsed["email"] == "user@outlook.com"
    assert parsed["clientId"] == client_id
    assert parsed["refreshToken"] == refresh_token
    assert parsed["authMethod"] == "graph"
