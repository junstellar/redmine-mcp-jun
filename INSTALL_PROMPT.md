# 🚀 설치 가이드

Redmine을 Claude Code에서 자연어로 다루게 해주는 MCP 서버. **두 줄이면 끝**, Windows·macOS·Linux 모두 지원.

---

## 방법 A — 가장 빠름 (직접 터미널 두 줄)

```bash
pipx install git+https://github.com/junstellar/redmine-mcp-jun.git
redmine-mcp-setup
```

진행 흐름:
1. pipx가 격리된 환경에 패키지 설치 (Python 3.10+ 필요)
2. `redmine-mcp-setup` 이 콘솔에서 **Redmine URL과 API 키**를 묻습니다 (키 입력 시 화면에 안 보임)
3. `~/.claude.json` 자동 백업 + redmine 항목 등록
4. Claude Code 완전 종료 후 재실행

**pipx가 없으면?**
- 권장: pipx 먼저 설치 → https://pipx.pypa.io/stable/installation/
- 또는 일반 pip: `pip install git+https://github.com/junstellar/redmine-mcp-jun.git` (Ubuntu 24.04+ 같이 PEP 668 차단 환경에서는 `pip install --user` 필요)

**API 키 받는 법**
> Redmine 로그인 → 우측 상단 '내 계정' → 'API 접근키 → 보기'

---

## 방법 B — Claude Code에 한 번 붙여넣기

Claude Code를 열어두고 **아래 박스 안의 내용을 통째로 복사 → 채팅창에 붙여넣기**.
터미널을 따로 열 필요가 없습니다.

````
이 PC에 Redmine MCP를 자동으로 설치해주세요. 처음부터 끝까지 자동 진행하고, 4번 단계에서만 사용자에게 Redmine URL과 API 키를 한 번 묻습니다.

## 설치 절차

1. `python --version` (Windows) 또는 `python3 --version` (Linux/Mac) 으로 Python 3.10 이상 확인. 없으면 https://www.python.org/downloads/ 에서 설치 후 PATH 추가하라고 안내하고 멈추세요.

2. **pipx 우선 시도:** `pipx --version` 으로 pipx 확인 → 있으면 `pipx install git+https://github.com/junstellar/redmine-mcp-jun.git` (이미 있으면 `pipx upgrade redmine-mcp`). pipx가 없으면 `pip install git+https://github.com/junstellar/redmine-mcp-jun.git` 시도. PEP 668 차단 메시지가 뜨면 `pip install --user ...` 로 재시도하거나 사용자에게 pipx 설치를 안내하세요.

3. `pip show redmine-mcp` (또는 `pipx list`)로 설치 성공 여부 확인.

4. 사용자에게 정확히 다음과 같이 묻고 응답을 기다리세요:

   ───────────────────────────────────────
   🔑 Redmine 주소와 API 키를 입력해주세요.

   - Redmine URL (예: https://redmine.example.com)
   - API 키: Redmine 로그인 → 우측 상단 '내 계정' → 'API 접근키 → 보기'

   ⚠️ 키가 이 채팅 세션에 한 줄 남습니다. 보안이 우려되면 설치 완료 후 Redmine에서 키를 재발급하세요.
   ───────────────────────────────────────

   사용자가 응답하면 즉시:

   ```
   redmine-mcp-setup --url "<사용자가_입력한_URL>" --api-key "<사용자가_입력한_키>" --force
   ```

5. 종료 코드 0이면 성공입니다. 사용자에게:

   ✅ 설치 완료. **Claude Code를 완전 종료 후 다시 실행**해주세요. 새 세션에서 `mcp__redmine__*` 도구 10개가 자동 활성화됩니다.

## 보안 규칙
- 4번 단계 외에는 키를 묻지 마세요.
- 사용자가 URL/키를 알려주기 전에는 `redmine-mcp-setup`을 실행하지 마세요.
````

---

## 보안 트레이드오프

| 방법 | 키 입력 위치 | 키가 남는 곳 |
|---|---|---|
| A (직접 터미널) | `getpass` 콘솔 입력 | 어디에도 안 남음 (`.claude.json` 외) |
| B (Claude 자동) | 채팅창 | 해당 Claude 세션 로그에 한 줄 |

A가 더 안전합니다. 키가 노출됐을까 우려되면 설치 후 Redmine **'내 계정 → API 접근키 → 초기화'** 로 재발급 + `redmine-mcp-setup --force` 로 새 키 등록.

---

## 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| `python` / `pip` 명령 못 찾음 | Python 미설치 또는 PATH 누락 | python.org 설치 시 "Add to PATH" 체크 / Linux는 `python3` / `pip3` 사용 |
| `error: externally-managed-environment` (PEP 668) | Ubuntu 24.04+, Debian 12+, 최신 Fedora/Arch | `pipx install ...` 사용 (또는 `pip install --user`) |
| `redmine-mcp-setup` 명령 못 찾음 | Scripts 경로 PATH 누락 | pipx: `pipx ensurepath` 후 셸 재시작 / 또는 `python -m redmine_mcp.installer` |
| `.claude.json` 없음 오류 | Claude Code 한 번도 실행 안 함 | Claude Code 한 번 열고 다시 시도 |
| MCP 도구가 안 보임 | Claude Code 재시작 안 함 | 완전 종료 후 재실행 |
| API 키 인증 실패 | 키 잘못 복사 / 비활성화 | '내 계정 → API 접근키 → 초기화' 로 재발급 |
