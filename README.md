# Redmine MCP Server

Claude Code(또는 다른 MCP 클라이언트)에서 **Redmine을 자연어로** 다룰 수 있게 해주는 MCP 서버.
Windows · macOS · Linux 모두 지원하는 **pip 패키지**입니다. 자체 호스팅(self-hosted) Redmine이든 사내 Redmine이든, API 접근키만 있으면 됩니다.

> ⚠️ API 키와 Redmine 주소는 **사용자 PC의 `~/.claude.json`에만** 저장됩니다. 서버는 stdio로 로컬에서만 동작하며, 외부로 키를 보내지 않습니다.

## 제공 도구 (10개)

| 도구 | 설명 |
|---|---|
| `list_projects` | 프로젝트 목록 |
| `list_issues` | 일감 목록 (프로젝트/담당자/상태/기간 필터) |
| `get_issue` | 이슈 상세 + 댓글 + 첨부 |
| `create_issue` | 새 이슈 생성 |
| `add_comment` | 이슈에 댓글 추가 (상태 변경 가능) |
| `list_wiki_pages` | 위키 페이지 목록 |
| `get_wiki` | 위키 페이지 조회 |
| `update_wiki` | 위키 페이지 생성/수정 |
| `get_my_today` | 나에게 할당된 일감 + 최근 갱신된 일감 (아침 알림용) |
| `list_enumerations` | 트래커/상태/우선순위 ID 목록 |

---

## 🚀 설치 — 두 줄 (Windows · macOS · Linux 공통)

### 사전 준비 (한 번만)
- Python 3.10 이상 ([python.org](https://www.python.org/downloads/) — 설치 시 "Add to PATH" 체크)
- `pipx` ([설치 가이드](https://pipx.pypa.io/stable/installation/))
- Claude Code를 1회 이상 실행 (`~/.claude.json` 자동 생성)
- Redmine API 접근키 (Redmine 로그인 → 우측 상단 '내 계정' → 'API 접근키')

### 설치 명령 (권장: pipx)

```bash
pipx install git+https://github.com/junstellar/redmine-mcp-jun.git
redmine-mcp-setup
```

`redmine-mcp-setup` 이 자동으로:
1. `~/.claude.json` 백업 (`~/.claude.json.backup.YYYYMMDD_HHMMSS`)
2. Redmine 서버 URL + API 키 입력받기 (키는 콘솔 비밀번호 입력 — 로그에 안 남음)
3. `mcpServers.redmine` 항목 등록

그 다음 **Claude Code 완전 종료 → 재실행** 하면 `mcp__redmine__*` 도구 10개가 활성화됩니다.

### 왜 pipx?
- CLI 도구를 격리된 환경에 설치 → 시스템 Python을 더럽히지 않음
- **PEP 668**(Ubuntu 23.04+, Debian 12+, 최신 Fedora 등) 환경에서 `pip install`이 차단되는 문제 회피
- 모든 OS에서 동일한 명령

### 업데이트 / 제거

```bash
pipx upgrade redmine-mcp          # 업데이트 후 Claude Code 재시작

redmine-mcp-uninstall             # .claude.json에서 항목 제거
pipx uninstall redmine-mcp
```

### 대안: 일반 pip (pipx 없을 때)

```bash
pip install git+https://github.com/junstellar/redmine-mcp-jun.git
redmine-mcp-setup
```

- PEP 668 차단 환경에서는 `pip install --user ...` 또는 가상환경 사용
- `pip`이 없으면 `pip3` / `python3 -m pip` 로 대체

---

## ⚡ 비대화식 설치 (자동화/배치)

```bash
redmine-mcp-setup --url "https://redmine.example.com" --api-key "여기에_API_키" --force
```

---

## 🐧 OS별 동작 상태

| 환경 | 상태 | 비고 |
|---|---|---|
| Windows 10/11 + Python 3.10~3.14 | ✅ 검증됨 | pip / pipx 모두 OK |
| macOS (Homebrew Python) | ✅ 표준 동작 | |
| Ubuntu 22.04 (Python 3.10) | ✅ 표준 동작 | |
| Ubuntu 24.04, Debian 12+, 최신 Fedora/Arch | ⚠️ **pipx 필수** | `pip install`은 PEP 668로 차단 |
| Ubuntu 20.04 등 Python 3.8 기본 | ⚠️ Python 업그레이드 필요 | `deadsnakes` PPA 또는 `pyenv`/`uv` |
| WSL2 | ✅ Linux와 동일 | |

**공통 요구사항:** Redmine API가 켜져 있고(관리 → 설정 → API), 해당 Redmine에 네트워크로 접근 가능해야 합니다. 사내/사설망 Redmine이라면 VPN 등으로 접근 가능한 상태여야 합니다.

---

## 활용 예시 (Claude Code 안에서)

조회
- "오늘 내 일감 정리해줘"
- "my-project 이슈 목록 보여줘"
- "123번 이슈 내용 뭐였지?"
- "이번 주에 갱신된 이슈 보여줘"
- "나에게 할당된 진행중 일감만 보여줘"

작성/수정
- "my-project에 'GPU 메모리 부족' 새 이슈 만들어줘"
- "#123 에 '진행 시작합니다' 라고 댓글 달아줘"
- "#123 상태를 종료로 바꿔줘"

위키
- "my-project 위키 페이지 목록 보여줘"
- "my-project 의 'Getting Started' 위키 페이지 만들어줘"

응용
- "어제 갱신된 내 일감 요약해서 메일 본문 형식으로 정리해줘"
- "지난 일주일 내 일감 상태별 개수 알려줘"

---

## 수동 설치 (스크립트 없이 직접 등록)

1. 패키지 설치
   ```bash
   pip install git+https://github.com/junstellar/redmine-mcp-jun.git
   ```

2. `~/.claude.json` 의 `mcpServers` 섹션에 추가:
   ```json
   {
     "mcpServers": {
       "redmine": {
         "command": "python",
         "args": ["-m", "redmine_mcp"],
         "env": {
           "REDMINE_URL": "https://redmine.example.com",
           "REDMINE_API_KEY": "여기에_본인_API_키",
           "PYTHONIOENCODING": "utf-8"
         }
       }
     }
   }
   ```
   * Windows: `%USERPROFILE%\.claude.json`
   * macOS/Linux: `~/.claude.json`

3. Claude Code 재시작

---

## 파일 구조

```
redmine-mcp/
├─ pyproject.toml          # pip 패키지 메타데이터
├─ src/
│  └─ redmine_mcp/
│     ├─ __init__.py
│     ├─ __main__.py       # python -m redmine_mcp
│     ├─ server.py         # MCP 서버 본체 (도구 10개)
│     └─ installer.py      # 설치/제거 스크립트
├─ install.ps1             # Windows 전용 wrapper (선택)
├─ uninstall.ps1           # Windows 전용 wrapper (선택)
├─ INSTALL_PROMPT.md       # Claude Code에 붙여넣어 자동 설치하는 프롬프트
├─ LICENSE                 # MIT
└─ README.md
```

## 직접 실행 테스트 (디버그)

stdio 모드라 직접 실행하면 클라이언트 입력을 기다리며 멈춥니다 (Ctrl+C로 종료).

```bash
REDMINE_URL=https://redmine.example.com \
REDMINE_API_KEY=여기에_키 \
redmine-mcp
```

Windows PowerShell:
```powershell
$env:REDMINE_URL="https://redmine.example.com"
$env:REDMINE_API_KEY="여기에_키"
redmine-mcp
```

---

## 라이선스

MIT — 자유롭게 사용·수정·배포하세요. 자세한 내용은 [LICENSE](LICENSE).
