"""
Redmine MCP Server

환경변수:
  REDMINE_URL      예: https://redmine.example.com
  REDMINE_API_KEY  Redmine "내 계정" 화면의 API 접근키

실행:
  redmine-mcp         # entry point (pip install 후)
  python -m redmine_mcp
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP, Image


mcp = FastMCP("redmine")

_client: Optional[httpx.Client] = None
_redmine_url: str = ""


def _ensure_client() -> httpx.Client:
    global _client, _redmine_url
    if _client is not None:
        return _client

    _redmine_url = os.environ.get("REDMINE_URL", "").rstrip("/")
    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not _redmine_url or not api_key:
        sys.stderr.write(
            "[redmine-mcp] 환경변수 REDMINE_URL, REDMINE_API_KEY 가 필요합니다.\n"
        )
        sys.exit(1)

    _client = httpx.Client(
        base_url=_redmine_url,
        headers={
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=20.0,
    )
    return _client


def _get(path: str, params: Optional[dict] = None) -> dict:
    r = _ensure_client().get(path, params=params)
    r.raise_for_status()
    return r.json()


def _post(path: str, payload: dict) -> dict:
    r = _ensure_client().post(path, json=payload)
    r.raise_for_status()
    return r.json() if r.content else {}


def _put(path: str, payload: dict) -> dict:
    r = _ensure_client().put(path, json=payload)
    r.raise_for_status()
    return r.json() if r.content else {}


def _fmt_dt(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return s[:19].replace("T", " ")


def _issue_brief(it: dict) -> dict:
    return {
        "id": it["id"],
        "subject": it["subject"],
        "tracker": it["tracker"]["name"],
        "status": it["status"]["name"],
        "priority": it["priority"]["name"],
        "author": it["author"]["name"],
        "assigned_to": it.get("assigned_to", {}).get("name"),
        "project": it["project"]["name"],
        "updated_on": _fmt_dt(it.get("updated_on")),
        "url": f"{_redmine_url}/issues/{it['id']}",
    }


@mcp.tool()
def list_projects() -> list[dict]:
    """Redmine 프로젝트 목록 조회 (식별자, 이름, 설명)."""
    d = _get("/projects.json", {"limit": 100})
    return [
        {
            "id": p["id"],
            "identifier": p["identifier"],
            "name": p["name"],
            "description": (p.get("description") or "").strip()[:200],
        }
        for p in d.get("projects", [])
    ]


@mcp.tool()
def list_issues(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: str = "open",
    updated_within_days: Optional[int] = None,
    tracker_id: Optional[int] = None,
    limit: int = 25,
    sort: str = "updated_on:desc",
) -> dict:
    """일감 목록 조회.

    Args:
        project_id: 프로젝트 식별자 (예: "my-project"). 비우면 전체.
        assigned_to: 담당자 ID 또는 "me" (본인).
        status: "open"(기본), "closed", "*"(전체) 또는 상태 ID.
        updated_within_days: 최근 N일 이내 갱신된 일감.
        tracker_id: 트래커 ID 필터.
        limit: 최대 개수 (기본 25, 최대 100).
        sort: 정렬 키 (기본 "updated_on:desc").
    """
    params: dict[str, Any] = {
        "status_id": status,
        "limit": min(limit, 100),
        "sort": sort,
    }
    if project_id:
        params["project_id"] = project_id
    if assigned_to:
        params["assigned_to_id"] = assigned_to
    if tracker_id:
        params["tracker_id"] = tracker_id
    if updated_within_days is not None:
        since = (datetime.now() - timedelta(days=updated_within_days)).strftime("%Y-%m-%d")
        params["updated_on"] = f">={since}"

    d = _get("/issues.json", params)
    return {
        "total_count": d.get("total_count", 0),
        "returned": len(d.get("issues", [])),
        "issues": [_issue_brief(it) for it in d.get("issues", [])],
    }


@mcp.tool()
def get_issue(issue_id: int, include_comments: bool = True) -> dict:
    """이슈 상세 조회 (본문 + 댓글 + 첨부파일).

    Args:
        issue_id: 이슈 번호 (예: 123).
        include_comments: 댓글 포함 여부 (기본 True).
    """
    include = ["attachments"]
    if include_comments:
        include.append("journals")

    d = _get(f"/issues/{issue_id}.json", {"include": ",".join(include)})
    it = d["issue"]

    comments = []
    if include_comments:
        for j in it.get("journals", []):
            note = (j.get("notes") or "").strip()
            if not note:
                continue
            comments.append({
                "id": j["id"],
                "author": j["user"]["name"],
                "created_on": _fmt_dt(j.get("created_on")),
                "notes": note,
            })

    attachments = [
        {
            "id": a["id"],
            "filename": a["filename"],
            "filesize": a.get("filesize", 0),
            "content_url": a["content_url"],
        }
        for a in it.get("attachments", [])
    ]

    return {
        "id": it["id"],
        "subject": it["subject"],
        "tracker": it["tracker"]["name"],
        "status": it["status"]["name"],
        "priority": it["priority"]["name"],
        "project": it["project"]["name"],
        "author": it["author"]["name"],
        "assigned_to": it.get("assigned_to", {}).get("name"),
        "created_on": _fmt_dt(it.get("created_on")),
        "updated_on": _fmt_dt(it.get("updated_on")),
        "start_date": it.get("start_date"),
        "due_date": it.get("due_date"),
        "done_ratio": it.get("done_ratio"),
        "description": it.get("description", ""),
        "comments": comments,
        "attachments": attachments,
        "url": f"{_redmine_url}/issues/{it['id']}",
    }


@mcp.tool()
def create_issue(
    project_id: str,
    subject: str,
    description: str = "",
    tracker_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    parent_issue_id: Optional[int] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
) -> dict:
    """새 이슈 생성.

    Args:
        project_id: 프로젝트 식별자 (예: "my-project") 또는 숫자 ID.
        subject: 제목 (필수).
        description: 본문 (Markdown 가능).
        tracker_id: 트래커 ID. list_enumerations() 로 확인.
        assigned_to_id: 담당자 사용자 ID.
        priority_id: 우선순위 ID.
        parent_issue_id: 상위 이슈 ID.
        start_date: 시작일 "YYYY-MM-DD".
        due_date: 마감일 "YYYY-MM-DD".
    """
    issue: dict[str, Any] = {
        "project_id": project_id,
        "subject": subject,
        "description": description,
    }
    for k, v in [
        ("tracker_id", tracker_id),
        ("assigned_to_id", assigned_to_id),
        ("priority_id", priority_id),
        ("parent_issue_id", parent_issue_id),
        ("start_date", start_date),
        ("due_date", due_date),
    ]:
        if v is not None:
            issue[k] = v

    d = _post("/issues.json", {"issue": issue})
    it = d["issue"]
    return {
        "id": it["id"],
        "subject": it["subject"],
        "url": f"{_redmine_url}/issues/{it['id']}",
        "message": "이슈 생성 완료",
    }


@mcp.tool()
def add_comment(issue_id: int, note: str, status_id: Optional[int] = None) -> dict:
    """이슈에 댓글 추가 (선택적으로 상태 변경).

    Args:
        issue_id: 이슈 번호.
        note: 댓글 내용 (Markdown 가능).
        status_id: 함께 변경할 상태 ID (없으면 상태 유지).
    """
    issue: dict[str, Any] = {"notes": note}
    if status_id is not None:
        issue["status_id"] = status_id

    _put(f"/issues/{issue_id}.json", {"issue": issue})
    return {
        "issue_id": issue_id,
        "url": f"{_redmine_url}/issues/{issue_id}",
        "message": "댓글 등록 완료",
    }


@mcp.tool()
def list_wiki_pages(project_id: str) -> list[dict]:
    """프로젝트의 위키 페이지 목록.

    Args:
        project_id: 프로젝트 식별자.
    """
    d = _get(f"/projects/{project_id}/wiki/index.json")
    return [
        {
            "title": p["title"],
            "version": p.get("version"),
            "parent": p.get("parent", {}).get("title"),
            "updated_on": _fmt_dt(p.get("updated_on")),
        }
        for p in d.get("wiki_pages", [])
    ]


@mcp.tool()
def get_wiki(project_id: str, page_name: str) -> dict:
    """위키 페이지 내용 조회.

    Args:
        project_id: 프로젝트 식별자.
        page_name: 페이지 제목.
    """
    d = _get(f"/projects/{project_id}/wiki/{page_name}.json")
    p = d["wiki_page"]
    return {
        "title": p["title"],
        "version": p.get("version"),
        "author": p.get("author", {}).get("name"),
        "created_on": _fmt_dt(p.get("created_on")),
        "updated_on": _fmt_dt(p.get("updated_on")),
        "text": p.get("text", ""),
        "url": f"{_redmine_url}/projects/{project_id}/wiki/{page_name}",
    }


@mcp.tool()
def update_wiki(
    project_id: str,
    page_name: str,
    text: str,
    comment: str = "",
    parent_title: Optional[str] = None,
) -> dict:
    """위키 페이지 생성/수정 (없으면 생성, 있으면 수정).

    Args:
        project_id: 프로젝트 식별자.
        page_name: 페이지 제목.
        text: 본문 (Textile 또는 Markdown).
        comment: 수정 사유.
        parent_title: 상위 페이지 제목 (계층 구조).
    """
    page: dict[str, Any] = {"text": text}
    if comment:
        page["comments"] = comment
    if parent_title:
        page["parent_title"] = parent_title

    _put(f"/projects/{project_id}/wiki/{page_name}.json", {"wiki_page": page})
    return {
        "project_id": project_id,
        "page_name": page_name,
        "url": f"{_redmine_url}/projects/{project_id}/wiki/{page_name}",
        "message": "위키 페이지 저장 완료",
    }


@mcp.tool()
def get_my_today() -> dict:
    """오늘 봐야 할 일감 한 번에 조회.

    - my_open_issues: 나에게 할당된 미완료 일감
    - recently_updated: 최근 2일 이내 갱신된 내 일감

    매일 아침 알림 스크립트에서 호출하기 좋게 구조화됨.
    """
    my_open = _get("/issues.json", {
        "assigned_to_id": "me",
        "status_id": "open",
        "limit": 50,
        "sort": "updated_on:desc",
    })

    since = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    recent = _get("/issues.json", {
        "assigned_to_id": "me",
        "status_id": "*",
        "updated_on": f">={since}",
        "limit": 50,
        "sort": "updated_on:desc",
    })

    def _brief(it: dict) -> dict:
        return {
            "id": it["id"],
            "subject": it["subject"],
            "project": it["project"]["name"],
            "status": it["status"]["name"],
            "priority": it["priority"]["name"],
            "updated_on": _fmt_dt(it.get("updated_on")),
            "url": f"{_redmine_url}/issues/{it['id']}",
        }

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "my_open_issues": {
            "count": my_open.get("total_count", 0),
            "items": [_brief(it) for it in my_open.get("issues", [])],
        },
        "recently_updated": {
            "count": recent.get("total_count", 0),
            "items": [_brief(it) for it in recent.get("issues", [])],
        },
    }


@mcp.tool()
def list_enumerations() -> dict:
    """이슈 생성/필터링에 필요한 ID 목록.

    - trackers: 트래커 (개발/버그/작업 등)
    - statuses: 상태 (신규/진행/종료 등)
    - priorities: 우선순위 (낮음/보통/높음 등)
    """
    trackers = _get("/trackers.json").get("trackers", [])
    statuses = _get("/issue_statuses.json").get("issue_statuses", [])
    priorities = _get("/enumerations/issue_priorities.json").get("issue_priorities", [])
    return {
        "trackers": [{"id": t["id"], "name": t["name"]} for t in trackers],
        "statuses": [
            {"id": s["id"], "name": s["name"], "is_closed": s.get("is_closed", False)}
            for s in statuses
        ],
        "priorities": [{"id": p["id"], "name": p["name"]} for p in priorities],
    }


_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}


@mcp.tool()
def download_attachment(attachment_id: int) -> Image:
    """첨부파일 다운로드 (이미지 인라인 표시).

    get_issue 결과의 attachments[].id 를 넘기면 이미지인 경우 대화창에 바로 렌더링됨.
    이미지가 아닌 첨부파일은 에러 — content_url 을 브라우저로 직접 열어주세요.

    Args:
        attachment_id: 첨부파일 ID.
    """
    meta = _get(f"/attachments/{attachment_id}.json")["attachment"]
    filename = meta["filename"]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _IMAGE_EXTS:
        raise ValueError(
            f"이미지가 아닙니다 ({filename}). content_url 을 직접 열어주세요: {meta.get('content_url')}"
        )

    r = _ensure_client().get(meta["content_url"])
    r.raise_for_status()

    fmt = "jpeg" if ext == "jpg" else ext
    return Image(data=r.content, format=fmt)


def main() -> None:
    """Entry point for `redmine-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
