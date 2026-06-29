"""
Cross-platform installer for redmine-mcp.

설치:
    redmine-mcp-setup

제거:
    redmine-mcp-uninstall
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows 콘솔에서 한글 깨짐 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SERVER_NAME = "redmine"


def _claude_json_path() -> Path:
    """Claude Code의 .claude.json 경로 (OS 무관, 홈 디렉토리 기준)."""
    return Path.home() / ".claude.json"


def _backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".backup.{stamp}")
    shutil.copy2(path, backup)
    return backup


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _resolve_command() -> str:
    """`.claude.json` 의 command 로 쓸 값.

    pip install 후 console_script로 생긴 redmine-mcp 실행파일 경로.
    PATH에 있으면 'redmine-mcp' 만으로 충분하지만, Claude Code가
    PATH를 못 따라오는 경우가 있어 절대 경로를 박는 게 안전.
    """
    found = shutil.which("redmine-mcp")
    if found:
        return found
    # Fallback: python -m redmine_mcp (entry script가 PATH에 없을 때)
    return sys.executable


def _resolve_args(command: str) -> list[str]:
    if command == sys.executable:
        return ["-m", "redmine_mcp"]
    return []


def install() -> int:
    parser = argparse.ArgumentParser(
        prog="redmine-mcp-setup",
        description="Register redmine MCP server in Claude Code config.",
    )
    parser.add_argument(
        "--api-key", help="Redmine API 키 (생략 시 대화식 입력)"
    )
    parser.add_argument(
        "--url", default="", help="Redmine 서버 URL (예: https://redmine.example.com)"
    )
    parser.add_argument(
        "--force", action="store_true", help="기존 redmine 항목을 덮어쓰기"
    )
    args = parser.parse_args()

    claude_json = _claude_json_path()
    print()
    print("===== Redmine MCP 설치 =====")
    print(f"대상 설정 파일: {claude_json}")
    print()

    if not claude_json.exists():
        print(
            "[오류] .claude.json 이 없습니다. Claude Code를 한 번 실행한 다음 다시 시도하세요.",
            file=sys.stderr,
        )
        return 1

    # Redmine URL
    url = (args.url or os.environ.get("REDMINE_URL", "")).strip()
    if not url:
        url = input("Redmine 서버 URL (예: https://redmine.example.com): ").strip()
    if not url:
        print("[오류] Redmine URL이 필요합니다.", file=sys.stderr)
        return 1

    # API 키
    api_key = args.api_key or os.environ.get("REDMINE_API_KEY", "")
    if not api_key:
        print("Redmine 우측 상단 '내 계정' → 'API 접근키' 에서 확인 가능")
        api_key = getpass.getpass("Redmine API 키: ").strip()

    if len(api_key) < 20:
        print(
            f"[오류] API 키가 너무 짧습니다 ({len(api_key)} 글자). 정확한 키를 입력하세요.",
            file=sys.stderr,
        )
        return 1

    # 백업
    backup = _backup(claude_json)
    print(f"백업 생성: {backup}")

    # 등록
    data = _load(claude_json)
    mcp_servers = data.setdefault("mcpServers", {})

    if SERVER_NAME in mcp_servers and not args.force:
        print(
            f"[경고] '{SERVER_NAME}' 항목이 이미 있습니다. 덮어쓰려면 --force 옵션을 사용하세요.",
            file=sys.stderr,
        )
        return 2

    command = _resolve_command()
    server_args = _resolve_args(command)
    mcp_servers[SERVER_NAME] = {
        "command": command,
        "args": server_args,
        "env": {
            "REDMINE_URL": url.rstrip("/"),
            "REDMINE_API_KEY": api_key,
            "PYTHONIOENCODING": "utf-8",
        },
    }
    _save(claude_json, data)

    print()
    print("===== 설치 완료 =====")
    print(f"  command: {command} {' '.join(server_args)}".rstrip())
    print(f"  Redmine URL: {url}")
    print()
    print("다음 단계:")
    print("  1. Claude Code 완전 종료 후 재실행")
    print("  2. 새 세션에서 '오늘 내 일감 보여줘' 등 자연어로 사용")
    print()
    print("문제 발생 시 백업 복원:")
    print(f'  python -c "import shutil; shutil.copy(r\'{backup}\', r\'{claude_json}\')"')
    print()
    return 0


def uninstall() -> int:
    parser = argparse.ArgumentParser(
        prog="redmine-mcp-uninstall",
        description="Remove redmine MCP server from Claude Code config.",
    )
    parser.parse_args()

    claude_json = _claude_json_path()
    if not claude_json.exists():
        print(".claude.json 이 없습니다.", file=sys.stderr)
        return 0

    data = _load(claude_json)
    mcp_servers = data.get("mcpServers", {})
    if SERVER_NAME not in mcp_servers:
        print(f"'{SERVER_NAME}' 항목이 등록되어 있지 않습니다.")
        return 0

    backup = _backup(claude_json)
    print(f"백업 생성: {backup}")

    del mcp_servers[SERVER_NAME]
    if not mcp_servers:
        data.pop("mcpServers", None)
    _save(claude_json, data)

    print(f"'{SERVER_NAME}' 항목 제거 완료. Claude Code 재시작 후 반영됩니다.")
    return 0


def main() -> None:
    sys.exit(install())


if __name__ == "__main__":
    main()
