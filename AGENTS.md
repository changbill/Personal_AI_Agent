# 프로젝트 에이전트 지침

## 하네스: CLAUDE.md ↔ AGENTS.md 동기화 (최우선 규칙)

**목표:** Claude Code와 Codex를 번갈아 사용하므로, 두 도구가 읽는 지침이 절대 어긋나지 않게 한다.

- `CLAUDE.md`와 `AGENTS.md`는 **바이트 단위로 동일해야 한다.** 도구별 예외 문구를 두지 않는다.
- 한쪽을 수정하면 **같은 작업 안에서** 다른 쪽에 그대로 반영한다. "나중에 맞추겠다"는 허용하지 않는다.
- 손으로 옮겨 적지 말고 파일 복사로 반영한다 (`cp CLAUDE.md AGENTS.md`). 손으로 옮기면 누락이 생긴다.
- 수정 후 `sh scripts/check_docs_sync.sh`로 검증한다. 이 스크립트가 실패하면 커밋하지 않는다.
- 이 규칙이 필요한 이유: 과거에 실제로 어긋난 적이 있다. `AGENTS.md`에서 `DOMAIN.md` 관련 항목 4개가 조용히 누락된 채 방치되었다.

## 프로젝트 개요

로컬 LLM 기반 멀티 에이전트 개인 비서. Linux 미니PC에서 상시 운영한다.

**가장 중요한 제약은 비용이다.** 개인 비서는 계속 실행되고 반복적으로 LLM을 호출하므로, 외부 유료 LLM API를 기본 모델로 쓰지 않는다. 설계 판단이 갈릴 때는 이 제약을 우선한다.

| 영역 | 선택 |
| --- | --- |
| Backend | Python 3.12+, FastAPI |
| Agent | Strands Agents SDK (`strands-agents[ollama]`) |
| LLM | Ollama + Qwen 소형 모델 (로컬 실행, 미니PC) |
| Session Memory | Redis (TTL 기반 단기 대화) |
| Long-term Memory | PostgreSQL (pgvector는 필요성이 확인되기 전까지 도입하지 않는다) |
| 패키지 관리 | uv (`pyproject.toml` + `uv.lock`) |
| 배포 | Docker Compose, Linux 미니PC |

Agent 구성: Orchestrator / Schedule / Search / General / Memory.

**로컬 소형 모델을 쓴다는 사실이 모든 설계에 스며든다.** 소형 모델의 한계는 모델을 키워서가 아니라 Application·Agent 설계로 보완한다. Agent에게 불필요하게 많은 Tool을 주지 않고, Context를 최소로 전달하며, LLM의 Structured Output을 그대로 신뢰하지 않고 Application에서 검증한다.

## 하네스: 크로스 툴 작업 연속성

**목표:** Claude Code와 Codex 중 어떤 도구로 세션을 시작하든, 이전 작업 맥락(계획·진행상황·인수인계)을 이어서 파악하고 작업할 수 있게 한다.

**세션 시작 시 반드시 먼저 읽을 것 (이 순서로):**

1. `.harness/HANDOFF.md` — 직전 세션이 어디서 멈췄는지
2. `.harness/STATE.md` — 지금까지 무엇이 완료되었는지
3. `.harness/ARCHITECTURE.md` — 기술 스택/구조 요약 (코드베이스 재탐색 최소화)
4. `.harness/DOMAIN.md` — Agent·Tool·Memory 판정 규칙 요약
5. `.harness/PLAN.md` — 제안·확정·진행 중인 계획
6. 필요 시 `.harness/DECISIONS.md`(과거 결정 이유), `.harness/BACKLOG.md`(미해결 항목)

**문서별 책임 (중복 기록 금지 — 아래 표에 없는 문서에는 해당 내용을 쓰지 않는다):**

| 문서 | 담는 내용 | 담지 않는 내용 |
| --- | --- | --- |
| `HANDOFF.md` | 세션마다 무엇을 했는지 (append-only 서술형 로그) | Phase 완료 요약(STATE 몫), 결정 이유(DECISIONS 몫) |
| `STATE.md` | 지금까지 끝난 것의 Phase 단위 요약 스냅샷 | 세션별 서술(HANDOFF 몫). 이슈를 하나하나 로그처럼 쌓지 않는다 — Phase가 끝나면 그 Phase 한 줄로 갱신 |
| `ARCHITECTURE.md` | 지금의 기술 스택/폴더 구조/컨벤션 (현재 상태) | 왜 그렇게 정했는지(DECISIONS 몫), 진행 상황(STATE 몫) |
| `DOMAIN.md` | 판정 규칙 현재 상태 — Agent 라우팅 기준, Tool 호출/비호출 조건, Long-term Memory 저장·중복·충돌 판정 기준 | 구현 진행 상황(STATE 몫), 결정 이유(DECISIONS 몫) |
| `DECISIONS.md` | 결정 내용과 이유의 역사(append-only) | 구현 여부/진행 상황(STATE 몫) |
| `PLAN.md` | 아직 안 끝난 계획과 체크리스트만 | 완료된 항목(체크만 남기지 말고 STATE로 옮긴 뒤 제거) |
| `BACKLOG.md` | 지금 하지 않지만 나중에 할 것(버그·기술부채·아이디어) | 진행 중인 계획(PLAN 몫) |

**작업 워크플로우 (필수):**

- 새로운 기능/변경 요청을 받으면, 바로 구현하지 말고 `.harness/PLAN.md`에 계획 초안을 작성한다.
- 사용자에게 계획을 제시하고 피드백을 받아 반영하는 과정을 반복한다.
- 사용자가 명시적으로 컨펌하면 계획을 확정 상태로 바꾸고 구현을 시작한다.
- 다음은 계획 절차 없이 바로 수행한다: 설명·조사·코드 리뷰처럼 파일을 변경하지 않는 요청, 오탈자나 명백한 단순 수정(수정 전 무엇을 바꾸는지 한 줄로 알린다).
- `PLAN.md` 체크리스트 항목은 하나씩 구현이 끝날 때마다 즉시 `.harness/STATE.md`에 반영하고, 그 항목을 `PLAN.md`에서 제거한다. `STATE.md`에는 위 표대로 Phase 단위 한 줄 요약만 남기고 세션 서술은 남기지 않는다.
- 구현 완료 후 `.harness/STATE.md`를 갱신한다.
- 세션을 종료하거나 작업을 중단할 때 `.harness/HANDOFF.md`에 다음 세션을 위한 인수인계를 남긴다.
- 아키텍처/워크플로우에 대한 중요한 결정을 내리면 `.harness/DECISIONS.md` 표의 최상단에 이유와 함께 기록해 최신 결정이 위에 오도록 유지한다.

**트리거:** 이 프로젝트에서의 모든 작업 요청에 위 워크플로우를 적용하라. 단순 질문(코드 설명 등)은 하네스 절차 없이 바로 응답 가능.

## 하네스: Phase 기반 진행

**목표:** 전체 기능을 한 번에 구현하지 않고, 검증 가능한 단위로 쌓는다.

- Phase 0 환경 검증 → 1 기본 Agent → 2 Multi Agent → 3 Tool Calling → 4 Session Memory → 5 Long-term Memory → 6 Memory Retrieval → 7 Memory 고도화(조건부) → 8 평가 → 9 미니PC 배포.
- 각 Phase **시작 전에** 다음을 사용자에게 제시한다: ① Phase 목표 ② 구현할 기능 ③ 추가/수정할 파일 ④ 주요 설계 결정 ⑤ 테스트 방법.
- 각 Phase **완료 후에** 다음을 정리한다: ① 구현된 기능 ② 테스트 결과 ③ CPU/RAM 등 운영 지표 ④ 발견된 문제 ⑤ 다음 Phase 내용.
- 한 Phase의 테스트가 통과한 것을 확인하기 전에 다음 Phase로 넘어가지 않는다.
- Phase 7(pgvector·Local Embedding)은 **필요성이 데이터로 확인된 경우에만** 착수한다. 미리 도입하지 않는다.

## 하네스: 변경 산출물 동기화

**목표:** 한 변경이 여러 산출물에 걸쳐 있을 때, 코드나 정책을 고치면서 관련 문서를 빠뜨리지 않는다.

**단일 소유권:**

| 정보 | 소유 산출물 |
| --- | --- |
| 개발 하네스 워크플로우, DB·테스트·브랜치·LLM 정책 | `CLAUDE.md` = `AGENTS.md` (동일 내용) |
| 크로스 툴 인수인계·진행 상황·아키텍처 현황·계획·결정·백로그 | `.harness/*.md` |
| Agent 라우팅·Tool 호출·Memory 판정 규칙 | `.harness/DOMAIN.md` |
| API wire 계약 | FastAPI 라우터 + Pydantic 스키마 코드 (OpenAPI는 코드에서 자동 생성하므로 별도 스펙 파일을 두지 않는다) |
| 의존성·Python 버전·툴 설정 | `pyproject.toml`, `uv.lock` |
| 런타임 구성(서비스·볼륨·네트워크·재시작 정책) | `docker-compose.yml`, `Dockerfile` |
| 환경변수 목록과 의미 | `.env.example` |
| 저장소 진입점, 커밋 컨벤션 안내 | 루트 `README.md` |

**변경 시 함께 갱신할 것:**

- **DB·테스트·브랜치·LLM 정책 변경**: `CLAUDE.md`와 `AGENTS.md`를 함께 수정하고, `.harness/ARCHITECTURE.md`의 관련 서술과 `.harness/DECISIONS.md`의 결정 이유를 갱신한다.
- **기술 스택·패키지 구조 변경**: `.harness/ARCHITECTURE.md`, 실제 `pyproject.toml`/`uv.lock`, 관련 테스트 설정을 함께 갱신한다.
- **API endpoint·요청/응답 스키마 변경**: Pydantic 스키마와 라우터를 함께 고치고, 호환성이 깨지면 `.harness/DECISIONS.md`에 근거를 남긴다. 계약 테스트도 같은 작업에서 갱신한다.
- **Agent 추가·삭제 또는 라우팅 기준 변경**: `.harness/DOMAIN.md`의 라우팅 규칙, Orchestrator system prompt, 평가 데이터셋(`tests/evaluation/`)의 기대 Agent를 함께 갱신한다.
- **Tool 추가·삭제 또는 Tool Description 변경**: `.harness/DOMAIN.md`의 Use when / Do not use when, 해당 Agent에 등록된 Tool 목록, 평가 데이터셋의 기대 Tool을 함께 갱신한다. **Tool Description 변경은 라우팅 정확도를 바꾸므로 평가를 다시 돌린다.**
- **Memory 저장·중복·충돌 판정 기준 변경**: `.harness/DOMAIN.md`, 검증 로직(threshold·allowed_types), 관련 테스트를 함께 갱신한다.
- **새 환경변수 도입**: `.env.example`에 키와 설명을 추가하고 설정 모듈에 반영한다. 실제 값은 절대 커밋하지 않는다.
- **README.md에 링크·안내가 걸린 파일을 이동·삭제·이름변경**: `README.md`의 해당 링크를 같은 작업에서 수정하거나 제거한다 (깨진 링크를 남기지 않는다).

**절차:**

1. 변경 전에 위 표에서 어떤 산출물이 영향을 받는지 식별한다.
2. 코드/정책 변경과 관련 산출물 갱신을 같은 작업(같은 커밋 또는 같은 PR)에서 처리한다.
3. 오래된 경로·이름·예제·상태를 검색해 남아있지 않은지 확인한다 (예: 파일을 삭제했다면 그 파일을 링크하던 다른 문서를 grep으로 확인).
4. 갱신한 산출물과 갱신하지 못한 산출물(권한 없음, 저장소에 없음 등)을 사용자에게 한국어로 보고한다. 존재하지 않는 산출물은 수정했다고 간주하지 않는다.

## 하네스: 툴체인 정책

**목표:** 어떤 도구로 작업하든 동일한 Python 환경과 명령을 쓴다.

- 패키지·가상환경 관리는 **uv**로 고정한다. 의존성은 `pyproject.toml`에 선언하고 `uv.lock`을 커밋한다. `pip install`을 직접 호출하지 않는다.
- 명령은 저장소 루트에서 `uv run ...` 형태로 실행한다 (예: `uv run pytest`, `uv run uvicorn app.main:app --reload`). 가상환경을 수동으로 activate하지 않아도 된다.
- 의존성 추가는 `uv add <pkg>`, 개발 전용은 `uv add --dev <pkg>`를 쓴다. `pyproject.toml`을 직접 편집한 뒤에는 `uv lock`으로 lock을 맞춘다.
- Python 최소 버전은 3.12로 잡는다 (Strands Agents SDK는 3.10 이상을 요구한다).
- Lint·format은 **ruff**(`uv run ruff check .`, `uv run ruff format .`)를 쓴다. 별도 flake8/black/isort를 추가하지 않는다.
- 타입 체크 도구는 아직 도입하지 않았다. 도입한다면 이 절과 `pyproject.toml`, CI 설정을 같은 작업에서 함께 갱신한다.
- **이미 존재하는 것:** `pyproject.toml`, `uv.lock`, `app/` 패키지, `tests/`, `.env.example`, `docker-compose.benchmark.yml`, `docker-compose.calendar.yml`.
- **아직 존재하지 않는 것:** `Dockerfile`, 통합 `docker-compose.yml`, `tests/evaluation/`. 이미 만들어졌다고 가정하고 참조하지 않는다. 각각 해당 Phase(9, 9, 8)에서 실제로 만든다.

## 하네스: 로컬 LLM 정책

**목표:** 소형 로컬 모델에서 Agent가 안정적으로 동작하게 하고, 미니PC 자원을 지키는 최소 규칙을 고정한다.

- 기본 LLM은 **Ollama 로컬 모델**이다. 외부 유료 LLM API를 기본 경로로 쓰지 않는다. 비교·평가 목적으로 잠시 쓰더라도 기본값으로 승격하지 않는다.
- 모델은 **태그를 명시**해서 고정한다 (예: `qwen3.5:2b-q4_K_M`). `latest` 태그를 쓰지 않는다 — 가리키는 대상이 바뀌면 평가 결과가 무의미해진다.
- **thinking 모드는 끄는 것을 기본으로 한다.** Ollama에서 thinking 지원 모델은 옵션 미지정 시 자동 활성화되고, Agent 라우팅처럼 짧은 판단만 필요한 호출에서 추론 지연을 크게 늘린다. 켜야 할 근거가 있는 호출에서만 예외로 켠다.
- **`num_ctx`를 명시적으로 낮게 설정한다.** 모델이 광고하는 최대 context를 그대로 쓰면 KV 캐시가 미니PC RAM을 잠식한다. 값은 평가로 정하고 `.harness/DECISIONS.md`에 근거를 남긴다.
- 불필요한 LLM 호출을 만들지 않는다. 규칙으로 판정 가능한 것(날짜 파싱, 형식 검증, 임계값 비교 등)은 LLM에 묻지 않고 코드로 처리한다.
- Context에 전체 세션이나 전체 Memory를 넣지 않는다. Session Memory는 최근 N개를 우선 쓰고 길어지면 요약하며, Long-term Memory는 현재 요청과 관련된 것만 선별해 주입한다.
- Agent 하나에 등록하는 Tool 수를 최소로 유지한다. Tool Description은 짧고 명확하게 쓰고, 호출 조건과 비호출 조건을 함께 적는다.
- **LLM의 Structured Output을 그대로 신뢰하지 않는다.** Agent는 판단만 하고, 저장 여부·범위·부작용의 최종 결정은 Application 코드가 검증 후 내린다.
- Phase 1에서 Strands `OllamaModel(host=..., model_id=..., additional_args={"think": False}, options={"num_ctx": 2048})`를 적용했다. SDK 요청 생성 코드와 미니PC Ollama 실호출 테스트로 전달 경로를 검증했다.

## 하네스: 외부 Tool·MCP 정책

**목표:** 외부 시스템을 Tool로 붙일 때 소형 모델의 Tool 선택 정확도와 비용 제약을 지킨다.

- 외부 시스템을 MCP로 붙일 때, **MCP 서버의 Tool을 Agent에 그대로 노출하지 않는다.** 자체 `@tool` 래퍼로 감싸고, Tool 이름·Description·호출/비호출 조건을 이 저장소가 소유한다. MCP 서버의 Description은 편집할 수 없고 비호출 조건이 없어, 소형 모델의 오선택을 막을 수단이 사라진다.
- MCP 서버가 노출하는 Tool 중 **실제로 쓰는 것만** 허용한다. `tool_filters`로 로드를 제한하고, Application도 허용 목록 외의 이름은 호출을 거부한다.
- **MCP 세션은 프로세스 단위로 열고 재사용한다.** 요청마다 서버를 띄우면 시작 지연이 매 턴에 붙고 인증 토큰 경합이 생긴다.
- **외부 Tool의 장애를 요청 실패로 만들지 않는다.** 연결 실패는 Tool 0개로 격리하고, Agent가 연결 불가를 말하게 한다. 동작하지 않는 Tool을 등록해 두면 모델이 가져오지 않은 결과를 사실처럼 말한다.
- **LLM이 제안한 Tool 인자를 검증 없이 외부 시스템에 넘기지 않는다.** 형식·범위·필수 필드를 Application이 판정하고, 위반은 Tool 실패로 반환한다.
- MCP 서버와 외부 컨테이너 이미지도 **태그를 고정한다.** 모델 태그와 같은 이유다 — 대상이 바뀌면 이전 측정과 비교할 수 없다.
- 외부 API는 무료 사용 범위가 충분한 것을 우선하고, 계정·카드가 필요한 제공자는 근거 없이 도입하지 않는다. 선택 근거는 `.harness/DECISIONS.md`에 남긴다.

## 하네스: DB 정책

**목표:** 저장소별 역할과 로컬·테스트·운영에서 사용할 엔진을 고정한다.

- 이 프로젝트의 유일한 RDB는 **PostgreSQL**이다. 로컬 실행, 테스트, 운영 모두 PostgreSQL을 사용한다. SQLite로 대체하지 않는다.
- **Redis는 Session Memory 전용이다.** TTL이 붙은 휘발성 대화 컨텍스트만 담는다. 사라지면 안 되는 데이터를 Redis에만 두지 않는다.
- **PostgreSQL은 Long-term Memory 전용이다.** 세션 종료 후에도 재사용할 가치가 있는 선호·습관·반복 패턴만 저장한다. 일회성 사실은 저장하지 않는다.
- **일정 데이터는 이 프로젝트의 DB에 저장하지 않는다.** Google Calendar가 유일한 출처다. 일정 테이블을 만들지 않는다.
- 두 저장소의 경계를 흐리지 않는다. Session Memory와 Long-term Memory를 같은 코드 경로에서 섞어 다루지 않는다.
- **pgvector는 아직 도입하지 않는다.** 초기 Retrieval은 `memory_type`/`key` 기반 검색으로 구현한다. 자연어 검색의 필요성이 평가 데이터로 확인되면 그때 Phase 7에서 도입하고, embedding 모델도 외부 유료 API보다 로컬 실행 가능한 것을 우선 검토한다.
- 로컬 개발 환경의 PostgreSQL과 Redis는 Docker로 실행한다.
- 접속 정보는 환경변수로 주입한다. 코드나 설정 파일에 기본값으로 넣지 않으며, 실제 값을 커밋하지 않는다.
- 스키마 마이그레이션 도구는 아직 도입하지 않았다. 첫 테이블을 만드는 시점에 정하고, 이 절과 `pyproject.toml`, 테스트 설정을 같은 작업에서 갱신한다.

## 하네스: 테스트 실행 정책

**목표:** 어떤 도구로 작업하든 검증 시 동일한 테스트 범위를 적용한다.

- 테스트 러너는 **pytest**다. 모든 명령은 저장소 루트에서 실행한다.
- 마커로 3계층을 구분한다. `pyproject.toml`의 `[tool.pytest.ini_options]`에 등록한다.

| 마커 | 대상 | 외부 의존 |
| --- | --- | --- |
| `unit` | 순수 로직 — 판정 함수, 검증 규칙, 스키마, 프롬프트 조립 | 없음 |
| `integration` | Redis·PostgreSQL 실제 동작 | 컨테이너 |
| `llm` | Ollama 로컬 모델 실제 호출 — 라우팅·Tool Calling·Structured Output | Ollama + 모델 |

- 구현·수정 후 **기본 검증은 단위 테스트만** 실행한다: `uv run pytest -m unit`.
- **TDD로 통합 테스트를 작성·수정하는 작업** 중에는 해당 통합 테스트를 반드시 실행한다 — red → green → refactor를 지킨다. 해당 파일만 실행해도 된다 (예: `uv run pytest tests/memory/test_memory_repository.py`).
- **전체 스위트**(`uv run pytest`)는 사용자가 명시적으로 요청했거나 CI에서 실행한다.
- **`llm` 마커 테스트는 기본 실행에서 제외한다.** 느리고 비결정적이며 Ollama가 떠 있어야 한다. 모델·프롬프트·Tool Description을 바꿨을 때와 평가 시점에 명시적으로 실행한다: `uv run pytest -m llm`.
- **평가(`tests/evaluation/`)는 pass/fail 테스트가 아니라 지표 측정이다.** 라우팅 정확도·Tool 선택 정확도·Memory 정확도·지연시간·CPU/RAM을 측정해 결과를 남긴다. 이걸 일반 테스트 스위트에 섞어 CI를 빨갛게 만들지 않는다.
- pytest 마커(`unit`, `integration`, `llm`)와 `tests/` 디렉터리는 Phase 1에서 구성했다.

## 하네스: 통합 테스트 구조

**목표:** Redis·PostgreSQL 실제 동작 검증은 유지하면서 기동 비용을 줄인다.

- 컨테이너는 **testcontainers-python**으로 띄우고, 세션 스코프 pytest fixture로 재사용한다. 테스트마다 새로 띄우지 않는다.
- fixture는 `tests/conftest.py`에 모은다. PostgreSQL fixture와 Redis fixture를 분리해, Redis만 필요한 테스트가 PostgreSQL을 띄우지 않게 한다.
- 테스트별 데이터 격리: PostgreSQL은 트랜잭션 롤백, Redis는 테스트마다 별도 key prefix 또는 DB 번호를 쓰고 종료 시 정리한다.
- `llm` 테스트는 컨테이너를 띄우지 않는다. 이미 실행 중인 Ollama에 붙고, 없으면 **실패시키지 말고 skip한다** (`pytest.skip`). 모델 없는 환경에서 스위트 전체가 깨지지 않게 한다.
- 위 구조는 아직 코드로 존재하지 않는다. Phase 4(Redis)와 Phase 5(PostgreSQL)에서 실제로 만든다. 이미 만들어졌다고 가정하고 참조하지 않는다.

## 하네스: 테스트 작성 원칙 (결과 검증 우선)

**목표:** 테스트가 내부 구현이 아니라 관찰 가능한 최종 결과(반환값·상태·예외)를 검증하게 하여, 리팩토링 내구성을 확보한다.

- 단위 테스트는 반환값, 변경된 상태, 발생한 예외를 검증하는 것을 기본으로 한다. Mock의 `assert_called_with()`는 "부작용이 실행됐는지/안 됐는지" 확인에만 쓴다.
- Mock으로는 결과 자체를 관찰할 수 없는 경우(동시성 등)는 실제 인프라를 쓰는 통합 테스트로 결과를 검증한다.
- 제어 불가능한 값(현재 시각, 난수, LLM 응답 등)은 로직 내부에서 직접 얻지 않고 파라미터나 의존성으로 주입받아 결정론적으로 동작하게 한다. **특히 LLM 호출을 판정 로직 안에 숨기지 않는다** — 숨기면 그 로직은 단위 테스트가 불가능해진다.
- 도메인 로직은 계산 후 상태 변경/값 반환까지만 책임지고, 저장·외부 호출 같은 부작용은 바깥 계층이 담당한다. 이렇게 분리하면 도메인 로직은 Mock 없이 입력→출력만으로 검증 가능하다.
- Memory 저장 판정, 중복·충돌 판정, confidence threshold 검증처럼 **Application이 소유하는 규칙은 반드시 `unit` 테스트로 덮는다.** LLM 응답은 고정된 샘플 dict를 입력으로 주면 되므로 Ollama 없이 검증할 수 있다.
- 언더스코어로 시작하는 비공개 함수/메서드는 직접 테스트하지 않는다. 검증이 필요할 만큼 복잡해졌다면 별도 단위로 뽑아 공개 계약으로 노출한다.
- 쿼리·SQL에 비결정적 함수나 하드코딩된 조건(기간 등)을 넣지 않고 파라미터로 받는다. 테스트는 "파라미터 → 결과" 계약을 검증하고, 쿼리 구현 자체(문법, 최적화 방식)는 검증 대상으로 삼지 않는다.
- **잘못된 Agent 라우팅과 잘못된 Tool Calling 사례를 발견하면 테스트로 남긴다.** 재발 방지가 목적이므로 고친 뒤에도 지우지 않는다.

## 하네스: DB 조회 원칙

**목표:** Memory가 쌓여도 조회가 선형으로 느려지지 않게 한다.

- Long-term Memory 조회에 전체 스캔을 쓰지 않는다. `(user_id, memory_type)`과 `(user_id, key)`에 인덱스를 둔다.
- 사용자 요청 하나를 처리하면서 Memory를 건건이 반복 조회하지 않는다. 필요한 것을 한 번에 가져온다 (N+1 방지).
- 조회 결과에 상한을 둔다. 관련 Memory가 많아도 Context에 들어가는 개수를 제한하고, 그 상한은 `.harness/DECISIONS.md`에 근거와 함께 남긴다.
- ORM을 쓸지 SQL을 직접 쓸지는 아직 정하지 않았다. Phase 5에서 정하고 이 절과 `pyproject.toml`, `.harness/ARCHITECTURE.md`를 같은 작업에서 갱신한다.

## 하네스: 로깅 정책

- 요청마다 다음을 기록한다: `user_id`, `session_id`, `selected_agent`, `tools_used`, Tool 실행 성공/실패, Agent 응답 시간, LLM 응답 시간, Memory 조회 여부, Memory 저장 여부, 오류 내용.
- **사용자 대화 원문 전체와 민감정보를 로그에 남기지 않는다.** 디버깅에 필요하면 길이·해시·요약처럼 원문이 아닌 형태로 남긴다.
- 로그는 나중에 평가 지표로 집계할 수 있게 구조화된 형태로 남긴다.

## 하네스: 브랜치·커밋 전략

**목표:** 어떤 도구로 작업을 시작하든 동일한 브랜치·커밋 규칙을 따른다.

- 원격 저장소는 `origin` (`https://github.com/changbill/Personal_AI_Agent.git`)이며 기본 브랜치는 `main`이다. `develop` 브랜치는 두지 않는다.
- 작업 브랜치는 `main`에서 분기한다. 이름은 Phase 작업이면 `phase{번호}/{설명}`(예: `phase0/environment-probe`), 그 외에는 `{타입}/{설명}`(예: `docs/agent-guidelines`)을 쓴다.
- **`main`에 직접 커밋하지 않는다.** 문서·설정 전용 작업도 코드 변경과 동일하게 브랜치에서 진행한다.
- 현재 브랜치가 진행 중인 작업과 다른 주제면, 구현 시작 전에 새 브랜치를 `main`에서 만들고 전환한다. 이미 해당 주제의 브랜치에 있다면 새로 만들지 않는다.
- 커밋 메시지 컨벤션:
  - `<타입>[적용 범위(선택)]: <제목>` 구조. 타입은 영어(`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`), 제목/본문은 한국어.
  - 제목은 명사형 어미로 끝내고 50자 이내, 마침표 없음.
  - scope는 작업 영역(예: `agent`, `memory`, `tools`, `infra`)을 명시하면 이력 추적에 유리하다.
  - 본문에는 "무엇을"보다 "왜"를 남긴다. 무엇을 바꿨는지는 diff가 말해준다.
- 커밋은 사용자가 명시적으로 요청했을 때만 생성한다. 관련 파일을 골라 stage하고, `git add .`/`git add -A`는 피한다.
- PR 생성과 push는 사용자가 명시적으로 요청했을 때만 수행한다.
- 브랜치 병합과 삭제는 자동으로 수행하지 않는다. PR 병합은 사용자가 직접 하거나, 사용자가 명시적으로 요청했을 때만 수행한다.
- 강제 push, `reset --hard`, `clean -fd`, `branch -D` 등 destructive 작업은 사용자의 명시적 허락 없이 수행하지 않는다.
- `.sh` 파일은 미니PC(Linux)에서 실행되므로 LF 개행을 유지한다. `.gitattributes`가 이를 강제하고 있으니 우회하지 않는다.

## 하네스: 보안·비밀값

- 환경변수와 credential을 코드에 하드코딩하지 않는다.
- `.env`는 커밋하지 않는다. 새 환경변수를 도입하면 `.env.example`에 키와 설명만 추가한다.
- 외부 API를 붙일 때는 무료 API 또는 무료 사용 범위가 충분한 서비스를 우선 검토하고, 선택 근거를 `.harness/DECISIONS.md`에 남긴다.

## 하네스: 불확실할 때의 행동

- 라이브러리 API나 Strands Agents SDK 사용법이 불확실하면 **추측해서 구현하지 않는다.** 현재 사용 중인 버전의 공식 문서나 실제 패키지 메타데이터를 확인한 뒤 구현한다.
- 확인하지 못한 것을 확인한 것처럼 서술하지 않는다. 문서와 보고 모두에서 "아직 검증하지 않음"을 명시한다.
- 성능이나 정확도가 개선되었다고 주장할 때는 반드시 평가 데이터로 근거를 제시한다. 인상이나 추정으로 개선을 주장하지 않는다.
- 존재하지 않는 파일·태스크·클래스를 "있다"고 서술하지 않는다. 아직 없으면 없다고 적고, 어느 Phase에서 만들지 함께 적는다.
