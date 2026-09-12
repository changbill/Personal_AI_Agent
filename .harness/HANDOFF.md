# HANDOFF — 세션별 인수인계 로그

> append-only. 새 항목을 **맨 아래에** 추가한다.
> 여기에는 "이번 세션에 무엇을 했고 다음 세션이 무엇부터 하면 되는지"만 적는다.
> Phase 완료 요약은 `STATE.md`, 결정 이유는 `DECISIONS.md`가 소유한다.

---

## 2026-09-10 — 세션 1 (Claude Code)

**브랜치:** `phase0/environment-probe`

### 한 일

1. **Phase 0 환경 조사.** 개발 머신(Windows 데스크톱) 사양·툴체인을 실측했다. `strands-agents` 1.54.0의 Ollama 연동 사양과 Ollama 라이브러리의 현재 Qwen 라인업을 공식 소스로 확인했다. 결과는 `ARCHITECTURE.md`와 `PLAN.md`에 있다.
2. **`scripts/phase0_probe.sh` 작성.** 미니PC 사양 측정용. 읽기 전용이고 coreutils 외 의존성이 없다. AVX/AVX2 지원 여부를 함께 검사한다 — CPU 추론 처리량을 크게 가르는 요소다.
3. **`.gitattributes` 추가.** `*.sh`를 LF로 고정. Windows에서 커밋해 Linux에서 실행하므로 CRLF가 섞이면 셔뱅이 깨진다.
4. **`CLAUDE.md` / `AGENTS.md` 재작성.** 이전 Java(Gradle/JPA/MSA) 프로젝트용 지침을 이 Python 프로젝트에 맞게 전면 개편했다. `scripts/check_docs_sync.sh`로 두 파일의 바이트 동일성을 검증한다.
5. **`.harness/` 문서 체계 신설.** 7개 문서를 지금까지의 조사 결과로 채웠다.

### 다음 세션이 할 일

**Phase 0은 아직 끝나지 않았다.** 다음 한 가지에 막혀 있다.

> **미니PC에서 `scripts/phase0_probe.sh`를 실행한 출력이 필요하다.**

사용자가 미니PC를 가지고 있다고 확인했고 사양을 알려주기로 했으나, 아직 받지 못했다. 출력을 받으면:

1. `ARCHITECTURE.md` 4.2절(현재 "미실측")을 실제 값으로 채운다.
2. MemAvailable과 AVX2 지원 여부로 `PLAN.md`의 모델 후보 A~E 중 실행 가능한 것을 좁힌다.
3. Phase 0-B(Ollama 설치 + 모델 벤치마크)로 진행한다.

### 주의할 것

- **개발 머신에서 모델 벤치마크를 돌리지 말 것.** 여기엔 GPU가 있고 미니PC엔 없을 가능성이 높아 결과가 이전되지 않는다. 사용자가 이 점을 명시적으로 지적했고, 그래서 이 머신에 Ollama를 설치하지 않았다. 근거는 `DECISIONS.md` 참조.
- **아직 애플리케이션 코드가 하나도 없다.** `pyproject.toml`도 `app/`도 `tests/`도 없다. 있다고 가정하고 참조하지 말 것.
- **thinking 모드 끄는 경로와 `num_ctx` 적용 여부는 미검증이다.** Strands 문서에서 확인하지 못했다. Phase 1에서 실제로 돌려보고 확인할 것. 추측으로 구현하지 말 것.
- `CLAUDE.md`를 고치면 반드시 `cp CLAUDE.md AGENTS.md` 후 `sh scripts/check_docs_sync.sh`로 검증할 것.

---

## 2026-09-10 — 세션 2 (Codex)

**브랜치:** `phase0/record-minipc-specs`

### 한 일

1. **미니PC 실측 결과를 문서에 반영했다.** Intel N150(4코어, AVX2), RAM 15GiB(측정 당시 MemAvailable 9GiB), 디스크 여유 48GiB, Intel 내장 GPU, Docker/Compose 실행 가능 상태를 `ARCHITECTURE.md` 4.2절에 기록했다.
2. **Phase 0-A를 완료로 전환했다.** `STATE.md`와 `PLAN.md`에서 미니PC 사양 수집 대기를 해소하고, 남은 작업을 Phase 0-B(Ollama 설치 방식 결정 및 모델 벤치마크)로 정리했다.

### 다음 세션이 할 일

1. Phase 0-B 시작 전 사용자에게 Ollama 벤치마크 계획(실행 방식, 후보 모델, 측정 항목, 변경 파일, 테스트 방법)을 제시하고 컨펌을 받는다.
2. 컨펌 후 Ollama를 CPU 기준으로 설치·실행하고 `qwen3.5:2b-q4_K_M`, `qwen2.5:3b`, 필요 시 `qwen3.5:4b-q4_K_M`을 순차 벤치마크한다.
3. 모델 태그 및 운영 설정이 확정되면 `DECISIONS.md`에 근거를 남기고 Phase 1로 넘어간다.

---

## 2026-09-10 — 세션 3 (Codex)

**브랜치:** `phase0/record-minipc-specs`

### 한 일

1. Phase 0-B CPU 벤치마크 구성을 추가했다: `docker-compose.benchmark.yml`, `scripts/benchmark_ollama.sh`, `benchmarks/phase0/RESULTS.md`.
2. Ollama 0.33.3 컨테이너를 기동하고 `qwen3.5:2b-q4_K_M`을 실측했다. 3회 평균은 15.19초, 4.20 tok/s, 컨테이너 메모리 스냅샷 2.33GiB다. 단일 도구 Tool Calling 및 JSON Structured Output도 확인했다.
3. `qwen2.5:3b`를 다운로드하고 비교 측정을 시작했다. 모델은 내려받았지만, 반복 측정 결과는 아직 문서화하지 않았다.

### 다음 세션이 할 일

1. `qwen2.5:3b`의 반복 성능·Tool Calling·Structured Output을 측정해 `benchmarks/phase0/RESULTS.md`에 기록한다.
2. 2B 결과와 비교해 4B 추가 평가 필요성을 판단한다. 모델 태그 및 운영 설정은 비교 데이터가 갖춰진 뒤 `DECISIONS.md`에만 확정한다.

---

## 2026-09-10 — 세션 4 (Codex)

**브랜치:** `phase1/basic-agent`

### 한 일

1. 사용자 컨펌 후 Phase 1의 FastAPI `POST /chat`, 단일 General Agent, 환경변수 설정, 구조화 로그, pytest 마커와 단위 테스트를 구현했다.
2. Strands 1.54.0 패키지 코드에서 `additional_args`가 Ollama chat 요청 최상위 인자로, `options`가 요청 options으로 전달되는 것을 확인했다. 코드에는 `think=false`, `num_ctx=2048`을 적용했다.
3. `uv run ruff check app tests`, `uv run pytest -m unit`은 통과했다. `uv run pytest -m llm`은 이 환경에 Ollama 환경변수·서버가 없어 skip됐다.

### 다음 세션이 할 일

미니PC에서 Ollama 환경변수를 설정한 뒤 `uv run pytest -m llm`을 실행한다. 통과하면 thinking·`num_ctx`의 실측 결과를 정책·아키텍처·결정 문서에 반영하고 Phase 1을 완료 처리한다. 현재 미추적 파일은 이 세션에서 만든 Phase 1 산출물이며, 사용자 요청 없이는 커밋하지 않는다.

---

## 2026-09-10 — 세션 5 (Codex)

**브랜치:** `phase1/basic-agent`

### 한 일

1. 실행 중인 `personal-ai-agent-ollama-benchmark` 컨테이너에서 `qwen3.5:2b-q4_K_M` 존재를 확인하고, `OLLAMA_HOST=http://127.0.0.1:11434`, `OLLAMA_NUM_CTX=2048`으로 llm 테스트를 실행했다. 12.54초에 통과했다.
2. `think=false` 및 `num_ctx=2048`의 Strands→Ollama 전달 경로를 SDK 코드와 실호출로 확인해 `CLAUDE.md`=`AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`에 반영했다.
3. Phase 1을 완료 처리했다. `ruff check`, unit 4개, llm 1개가 통과했고, `uv lock --check`, 문서 동기화, diff 공백 검사도 통과했다.

### 다음 세션이 할 일

Phase 2를 시작하려면 사용자에게 Multi Agent의 목표·파일·라우팅 설계·테스트 방법을 먼저 제시하고 컨펌을 받는다.

---

## 2026-09-10 — 세션 6 (Codex)

**브랜치:** `feat/external-chat-access`

### 한 일

1. `GET /`에 최소 브라우저 채팅 화면을 추가했다. 화면은 같은 origin의 `POST /chat`만 호출하며 `/docs`는 유지된다.
2. 외부 hostname `personal-agent.changee.cloud`, loopback Uvicorn 실행 방법 및 Cloudflare Tunnel/Access 설정 조건을 README와 하네스 문서에 기록했다. token·credential은 기록하지 않았다.
3. `uv run ruff format --check app tests`, `uv run ruff check app tests`, `uv run pytest -m unit`을 실행해 통과했다 (unit 5 passed, llm 1 deselected).

### 다음 세션이 할 일

사용자가 Cloudflare Tunnel·Access 및 외부 브라우저 접근을 확인해 완료 처리했다. 다음 작업은 Phase 2이며, 시작 전 사용자에게 목표·파일·라우팅 설계·테스트 방법을 제시하고 컨펌을 받는다.

---

## 2026-09-11 — 세션 7 (Codex)

**브랜치:** `feat/external-chat-access`

### 한 일

1. 사용자가 Cloudflare Tunnel·Access 설정과 인증된 외부 HTTPS 채팅 요청, 미인증 접근 차단을 확인했다고 보고했다.
2. 외부 Chat 접근 계획을 완료 처리하고, 현재 아키텍처·Phase 1 완료 상태를 동기화했다.
3. 커밋 전 검증으로 unit 테스트 5개 통과, ruff 검사·포맷 검사, 문서 동기화, lock 검사를 통과했다.

### 다음 세션이 할 일

Phase 2를 시작하려면 사용자에게 Multi Agent의 목표·파일·라우팅 설계·테스트 방법을 먼저 제시하고 컨펌을 받는다.


---

## 2026-09-12 — 세션 8 (Codex)

**브랜치:** `feat/env-file-settings`

### 한 일

1. `python-dotenv`를 추가하고 `Settings.from_env()`가 저장소 루트의 gitignore된 `.env`를 자동 로드하도록 변경했다. 이미 주입된 셸 환경변수는 덮어쓰지 않는다.
2. 운영용 `.env`에 Ollama host·고정 모델 태그·context 값을 등록하고, `.env.example`·README·아키텍처·결정 문서를 갱신했다.
3. `.env` 자동 로드와 셸 환경변수 우선순위를 unit 테스트로 추가했다. `ruff`, unit 테스트(6 passed), lock·문서 동기화 검증을 통과했고, 새 설정으로 Uvicorn을 재기동해 `127.0.0.1:8000`의 HTTP 200을 확인했다.

### 다음 세션이 할 일

인증된 외부 브라우저에서 Cloudflare Tunnel 뒤 채팅 요청을 확인한다. 장기적으로는 Phase 9에서 자동 재시작 배포 구성을 만든다.

---

## 2026-09-12 — 세션 9 (Codex)

**브랜치:** `feat/env-file-settings`

### 한 일

1. 모든 `POST /chat` 요청을 General Agent로 고정하던 동작을 Phase 2 규칙 기반 Orchestrator로 교체했다. Schedule/Search/General 중 하나만 선택하고, 복합 요청과 비정상 선택은 General로 폴백한다.
2. Tool 없는 Schedule/Search 전문 Agent와 라우팅 서비스를 추가하고, API 구조화 로그에 실제 선택 Agent를 남기도록 변경했다.
3. unit 14개와 실제 Ollama llm 테스트 1개, ruff, 문서 동기화, lock 검증을 통과했다.

### 다음 세션이 할 일

Phase 3 Tool Calling을 시작하려면 사용자에게 목표·파일·Tool 계약·테스트 방법을 제시하고 컨펌을 받는다.

---

## 2026-09-12 — 세션 10 (Claude Code)

**브랜치:** `phase3/tool-calling`

### 한 일

1. **Phase 3를 3-A / 3-B로 쪼개 계획을 세우고 사용자 컨펌을 받았다.** 3-B(`search_web`·`search_place`)를 분리한 이유는 무료 제공자가 없기 때문이다. Brave 무료 tier가 2026년 2월에 폐지되어 카드 등록 후 월 $5 크레딧제로 바뀌었고, 나머지 후보는 계정·낮은 쿼터 또는 미니PC 자원 상시 점유를 요구한다.
2. **일정 관리를 Google Calendar MCP 연결로 구현했다.** 사용자가 자체 저장소 대신 Google Calendar를 원했다. 커뮤니티 서버 `@cocal/google-calendar-mcp` v2.6.3을 Docker로 빌드해 streamable HTTP로 붙인다. 공식 Google Workspace MCP는 원격 서버이고 유료 플랜을 요구해 제외했다.
3. **MCP Tool을 그대로 노출하지 않고 자체 `@tool` 래퍼로 감쌌다.** MCP 서버가 Description을 소유하면 LLM이 보는 설명이 편집 불가능한 영어 한 줄이 되고 비호출 조건을 붙일 수 없다. 래퍼가 Tool 이름과 한국어 Description을 소유하므로 `DOMAIN.md` 설계와 코드가 일치한다. 생성된 `tool_spec`을 실제로 출력해 Description·필수 인자·파라미터 설명이 의도대로 들어갔는지 확인했다.
4. **Agent 반환 계약을 `AgentReply(text, tool_calls)`로 교체했다.** 이전에는 `str(agent(message))`로 `AgentResult`를 버려서 `tools_used`가 항상 빈 배열이었다. 이제 `metrics.tool_metrics`에서 호출 횟수·성공 횟수를 읽어 `tools_used`와 `tools_failed`를 실제 값으로 남긴다.
5. **Strands 1.54.0 sdist를 내려받아 Tool·MCP 사양을 직접 확인했다.** 결과는 `ARCHITECTURE.md` 3.1절에 있다. 공식 문서 URL은 404였다. `original_function` 같은 속성은 없고 데코레이터 객체를 그대로 호출하면 된다.
6. **개발 머신(Windows)에 uv 0.12.13을 설치했다.** 이전까지 검증이 미니PC에서만 가능했다. `ruff format`·`ruff check` 통과, unit 100개 통과.
7. 문서를 갱신했다: `DOMAIN.md`(Tool 계약·검증 규칙), `ARCHITECTURE.md`(디렉터리 현황·SDK 사양·런타임), `DECISIONS.md`(결정 8건), `STATE.md`, `PLAN.md`, `BACKLOG.md`, `CLAUDE.md`=`AGENTS.md`(외부 Tool·MCP 정책 신설, DB 정책에 일정 데이터 항목 추가, 스테일했던 "아직 존재하지 않는 것" 목록 수정).

### 다음 세션이 할 일

**Phase 3-A는 코드가 끝났고 실연동만 남았다. 사용자 작업이 선행되어야 한다.** `PLAN.md`의 체크리스트를 그대로 따르면 된다.

1. 사용자가 Google Cloud 프로젝트·Calendar API·OAuth Desktop app 자격증명을 만들고 `secrets/gcp-oauth.keys.json`에 둔다.
2. 미니PC에서 `docker compose -f docker-compose.calendar.yml up -d --build`를 실행한다. 공개 이미지가 없어 첫 실행에 Node 빌드가 일어난다.
3. 최초 OAuth 동의는 브라우저가 필요하다. 미니PC는 loopback 전용이므로 SSH 포트 포워딩으로 승인한다.
4. `.env`에 `CALENDAR_MCP_URL`을 넣고 `uv run pytest -m llm`을 돌린다.

### 주의할 것

- **실제 캘린더 연동은 검증하지 않았다.** OAuth 자격증명이 없어서다. 단위 테스트는 기록된 MCP 응답 형태로만 검증했다. 동작한다고 서술하지 말 것.
- **Open-Meteo 실제 네트워크 호출도 미검증이다.** 응답 샘플 파싱만 검증했다.
- **2B 모델의 Tool 선택 정확도를 측정하지 않았다.** Tool 4개는 사용자가 선택한 값이며, 오선택률은 Phase 8 평가 대상이다.
- **Tool Description을 고치면 `uv run pytest -m llm`을 다시 돌려야 한다.** Description이 Tool 선택 로직이기 때문이다.
- 캘린더 MCP 서버 태그를 올리면 `app/tools/calendar_tools.py`의 MCP 인자 매핑을 함께 확인해야 한다. 단위 테스트가 매핑을 고정하고 있다.
- `secrets/`와 `*.keys.json`은 `.gitignore`에 추가했다. 자격증명을 커밋하지 말 것.
- 이 세션은 커밋하지 않았다. 사용자 요청이 없었다.

---

## 2026-09-13 — 세션 11 (Claude Code)

**브랜치:** `phase3/tool-calling`

### 한 일

1. **세션 10에서 내가 넣은 날짜 결함을 찾아 고쳤다.** `date.today()`는 OS 로컬 시간대를 따르는데 `AGENT_TIMEZONE`은 프롬프트 문자열로만 쓰이고 있었다. 호스트가 UTC면 한국 시간 자정부터 오전 9시까지 주입 날짜가 하루 밀린다. 실측으로 확인했다 — 같은 순간에 `Asia/Seoul`은 2026-09-13, `UTC`는 2026-09-12였다. 이제 `build_today_clock(timezone)`이 지정된 시간대로 날짜를 계산하고, 두 전문 Agent의 `today` 인자는 기본값 없는 필수 인자로 바꿔 잘못된 기본값이 다시 생기지 않게 했다.
2. **`get_current_time` Tool을 추가했다.** 사용자 요청대로 외부 API에서 시각을 가져온다. 등록 대상은 General Agent뿐이다. Schedule·Search는 프롬프트 주입을 유지했다 — 일정 조회 한 번에 모델 왕복이 둘이 되면 4.2 tok/s 환경에서 약 15초가 더 붙고, 모델이 시간 Tool을 건너뛰면 날짜를 지어낸다. 사용자와 이 선택을 확인했다.
3. **시각 API를 실제로 호출해 고르고 검증했다.** `worldtimeapi.org`는 서비스가 종료되어 연결이 리셋된다. `timeapi.world`는 조사한 경로에서 404였다. `timeapi.io`만 키 없이 동작했다. Asia/Seoul·UTC·America/New_York 세 시간대로 실호출해 오프셋이 맞는지 확인했고, 강제 실패를 넣어 로컬 폴백도 확인했다.
4. **`tzdata`를 의존성에 추가했다.** Windows에는 IANA 시간대 DB가 없어 `zoneinfo`가 실패한다. 개발 머신과 미니PC의 동작을 같게 하려면 필요하다. `AGENT_TIMEZONE`은 기동 시점에 유효성을 검증한다.
5. **JSON fetcher를 `app/services/http_client.py`로 분리했다.** 날씨·시간 서비스가 같은 fetcher를 쓴다. 중복 구현을 막았다.
6. 문서를 갱신했다: `DOMAIN.md`(Tool 표, 2.4절을 Agent별 날짜 경로로 재작성, 2.5절 시간 조회 폴백 신설), `ARCHITECTURE.md`(timeapi.io 사양, tzdata, 디렉터리), `DECISIONS.md`(결정 4건), `STATE.md`, `PLAN.md`.

### 다음 세션이 할 일

**Phase 3-A는 여전히 실연동 검증만 남았다.** `PLAN.md`의 체크리스트를 따르면 된다. 이번 세션에서 두 항목이 추가됐다.

1. 사용자가 Google OAuth 자격증명을 만들어야 캘린더 검증을 시작할 수 있다. 이 부분은 세션 10 이후 변동 없다.
2. 미니PC의 OS 시간대를 `timedatectl`로 확인한다. UTC라면 이번 수정이 실제 차이를 만든다. 코드는 이제 OS 설정과 무관하게 `AGENT_TIMEZONE`을 따른다.
3. `uv run pytest -m llm`을 돌리면 시간 Tool 테스트 2개가 추가로 실행된다. 하나는 "오늘 며칠이야"에 Tool을 부르는지, 하나는 무관한 대화에서 부르지 않는지 본다.

### 주의할 것

- **`PLAN.md`에 다른 세션이 추가한 "한국어 지명 해석" 계획이 컨펌 대기 상태로 들어 있다.** 내가 쓴 것이 아니고 손대지 않았다. Open-Meteo Geocoding이 한국어 지명을 제대로 못 찾는다는 실측 표가 함께 있다. 이어서 작업할 때 먼저 확인할 것.
- 그 세션이 Open-Meteo 실호출을 확인했다고 적어, `PLAN.md`의 "미검증" 목록에 있던 Open-Meteo 항목과 모순됐다. 미검증 목록에서 그 줄을 제거했다.
- **timeapi.io의 무료 사용 한도는 문서에 없다.** 확인하지 못했다. 한도에 걸리면 로컬 시계로 폴백해 동작은 유지되지만, 그 사실을 알고 있어야 한다.
- **General Agent가 Tool을 갖게 된 것은 설계 변경이다.** 이전까지 의도적으로 0개였다. 무관한 대화에서 시간 Tool을 부르는 오선택이 새 위험이며, `-m llm` 테스트 하나가 이것을 감시한다. 실제 비율은 Phase 8 평가 대상이다.
- 이 세션은 커밋하지 않았다. 사용자 요청이 없었다.

---

## 2026-09-13 — 세션 12 (Claude Code)

**브랜치:** `phase3/tool-calling`

### 한 일

1. **Open-Meteo 실호출을 검증했다.** `PLAN.md`에 미검증으로 남아 있던 항목이다. 날씨는 이미 런타임에 실제 HTTP fetcher로 주입돼 있었고, 조회·파싱 경로가 실제로 동작한다.
2. **검증 과정에서 한국어 지명이 해석되지 않는 결함을 발견했다.** Geocoding 색인이 로마자여서 `language=ko`로도 한국어 이름이 검색되지 않는다. "서울"·"제주"는 0건, "대전"은 전라남도의 동명 지역, "부산"은 경상북도의 동명 지역이 1순위였다. 0건보다 동명 오답이 더 나쁘다 — 모델이 엉뚱한 지역 날씨를 사실처럼 답한다.
3. **사용자 컨펌 후 `app/services/place_directory.py`를 추가했다.** 한국 17개 시·도와 주요 시 47개의 지명→좌표 표다. 접미사(`특별시`·`시`·`도` 등)를 떼고 다시 찾되 뗀 결과가 표에 있을 때만 뗀다 (`대구`를 `대`로 자르지 않기 위함). `도` 단위 질의는 도청 소재 도시로 해석하고 답변에 그 도시 이름을 남긴다.
4. **좌표를 내 기억이 아니라 Open-Meteo에서 뽑았다.** 로마자 이름으로 조회해 행정구역(`admin1`)이 맞는 결과만 남기고 인구가 가장 많은 항목을 골랐다. 예보 격자가 API가 골랐을 지점과 같아진다. 독립적으로 두 번 수집해 47개 좌표가 전부 일치하는 것을 확인했다.
5. **Geocoding 폴백에서 한글 질의는 `country_code == "KR"`를 우선하도록 했다.** 표에 없는 읍·면·동을 한국어로 물을 때 동명 해외 지명이 1순위로 오는 것을 막는다. 후보 수를 1개에서 5개로 늘렸다.
6. 중복이던 `Place` 정의를 `place_directory`로 모으고 `weather_service`가 가져다 쓰게 했다.
7. 문서를 갱신했다: `DOMAIN.md`(지명 해석 판정 순서 표), `DECISIONS.md`(결정 2건), `STATE.md`, `PLAN.md`.

### 검증 결과

- `ruff format`·`ruff check` 통과. unit 135개 통과.
- 실호출: 서울·서울특별시·부산·대전·제주도·경기도·인천이 모두 올바른 광역 좌표로 해석됐다. 표에 없는 "학동"은 KR 우선 폴백으로, "도쿄"·"Paris"는 기존 경로로 조회됐다. "없는도시"는 Tool 실패로 떨어졌다.

### 다음 세션이 할 일

Phase 3-A의 남은 것은 여전히 캘린더 실연동이다. `PLAN.md` 체크리스트를 따르면 된다.

### 주의할 것

- **Tool Description은 바꾸지 않았으므로 `-m llm` 재실행은 필요 없다.** 지명 해석은 Description 아래의 구현이다. Description을 고치면 다시 돌려야 한다.
- **표의 범위는 17개 시·도와 주요 시까지다.** 읍·면·동은 Geocoding 폴백이 담당하며, 그 경로의 정확도는 측정하지 않았다.
- **`광주`는 광주광역시로 해석된다.** 경기도 광주시를 물으면 틀린 답이 나온다. 동명 광역시·기초시가 있는 지명의 일반적 한계이며, 실사용에서 문제가 되면 그때 다루면 된다.
- 이 세션은 커밋하지 않았다. 사용자 요청이 없었다.
