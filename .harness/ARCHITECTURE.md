# ARCHITECTURE — 기술 스택·구조 현재 상태

> 이 문서는 **지금 어떤 상태인지**만 담는다. 왜 그렇게 정했는지는 `DECISIONS.md`, 진행 상황은 `STATE.md`가 소유한다.
> 아직 존재하지 않는 것은 "없음"으로 적는다. 있다고 가정해서 쓰지 않는다.

최종 갱신: 2026-09-12

## 1. 코드베이스 현황

**Phase 3-A의 Tool Calling 코드까지 존재한다.** 현재 저장소 구성은 다음과 같다.

| 경로 | 내용 |
| --- | --- |
| `CLAUDE.md` / `AGENTS.md` | 에이전트 지침 (바이트 동일 유지) |
| `.harness/*.md` | 크로스 툴 작업 연속성 문서 |
| `scripts/phase0_probe.sh` | 미니PC 사양 측정 (읽기 전용) |
| `scripts/check_docs_sync.sh` | CLAUDE.md ↔ AGENTS.md 동일성 검증 |
| `.gitattributes` | `*.sh`·Dockerfile·yml을 LF로 고정 |
| `.gitignore` | GitHub 표준 Python 템플릿 |
| `README.md` | 스텁 (제목 한 줄) |
| `LICENSE` | — |
| `app/` | FastAPI 진입점, 규칙 기반 Orchestrator·Schedule/Search/General Agent, 일정·날씨 Tool, 캘린더 MCP 게이트웨이, 프로세스 런타임, 설정·구조화 로그, 브라우저 채팅 정적 자산 |
| `tests/` | unit 100개 + llm 3개 |
| `docker-compose.calendar.yml` | Google Calendar MCP 서버 (git 태그 `v2.6.3`에서 빌드) |
| `pyproject.toml` / `uv.lock` | Python 3.12 의존성·고정된 잠금 파일. `tzdata`는 Windows `zoneinfo`용 |
| `.env.example` | Ollama·시간대·캘린더 환경변수 예시. gitignore된 `.env`는 실행 시 자동 로드 |

없는 것: `Dockerfile`, 통합 `docker-compose.yml`(Phase 9), `tests/evaluation/`(Phase 8).

## 2. 디렉터리 구조

현재 존재하는 것:

```
app/
├── main.py                      FastAPI 진입점, 종료 시 MCP 세션 정리
├── api/            chat.py
├── agents/         orchestrator.py, schedule_agent.py, search_agent.py,
│                   general_agent.py, prompts.py, reply.py, model_factory.py
├── tools/          calendar_tools.py, weather_tools.py, time_tools.py
├── models/         schedule.py
├── services/       orchestrator_service.py, runtime.py, calendar_gateway.py,
│                   weather_service.py, time_service.py, http_client.py
├── core/           config.py, logging.py
└── web/            index.html, chat.css, chat.js

tests/
├── agents/  core/  models/  services/  tools/
```

아직 없는 것 (해당 Phase에서 만든다):

```
app/
├── agents/         memory_agent.py                            Phase 5
├── tools/          search_tools.py, memory_tools.py           Phase 3-B, 5
├── memory/         session_memory.py, long_term_memory.py,
│                   memory_extractor.py, memory_retriever.py   Phase 4~6
├── repositories/   memory_repository.py                       Phase 5
└── models/         memory.py                                  Phase 5

tests/
├── memory/                                                    Phase 4~6
└── evaluation/                                                Phase 8
```

## 3. 확정된 외부 의존성 사양 (실측 확인함)

`strands-agents` **1.54.0** — 2026-09-10 PyPI 메타데이터로 확인

- Python 요구: **>= 3.10** (이 프로젝트는 3.12로 잡음)
- Ollama 연동 extra 존재: `pip install 'strands-agents[ollama]'` → uv 기준 `uv add 'strands-agents[ollama]'`
- 선언된 extras: a2a, all, anthropic, bidi 계열, cedar, dev, docs, gemini, litellm, llamaapi, mistral, **ollama**, openai, otel, sagemaker, writer

`strands.models.ollama.OllamaModel` 생성자 파라미터 (공식 문서 확인)

| 파라미터 | 타입 | 기본값 |
| --- | --- | --- |
| `host` | str | 필수 |
| `model_id` | str | 필수 |
| `keep_alive` | str | `"5m"` |
| `max_tokens` | int \| None | None |
| `temperature` | float \| None | None |
| `top_p` | float \| None | None |
| `stop_sequences` | list \| None | None |
| `options` | dict \| None | None |
| `additional_args` | dict \| None | None |

동작상 주의점 2가지 (문서 명시)

- Structured Output은 Pydantic 모델을 **tool spec으로 변환**한다. 따라서 **tool calling을 지원하지 않는 모델에서는 Memory Agent의 Structured Output이 동작하지 않는다.**
- Ollama는 단일 메시지 안의 content block 배열을 지원하지 않아, SDK가 멀티파트 메시지를 별도 메시지로 평탄화한다.

Strands 1.54.0에서 `additional_args={"think": False}`는 Ollama chat 요청의 최상위 인자로, `options={"num_ctx": 2048}`은 요청 options로 전달됨을 패키지 코드와 미니PC 실호출로 확인했다.

### 3.1 Tool·MCP 사양 (1.54.0 sdist에서 직접 확인)

| 항목 | 확인 결과 |
| --- | --- |
| Tool 정의 | `from strands import tool`. `@tool` 또는 `@tool(name=..., description=...)` |
| Tool 등록 | `Agent(tools=[...])`. 함수·모듈·`ToolProvider` 인스턴스를 받는다 |
| 생성되는 스펙 | 이름·설명은 데코레이터 인자, 파라미터 스키마는 타입 힌트, 파라미터 설명은 docstring `Args:`에서 나온다 |
| 직접 호출 | 데코레이터가 붙은 객체를 그대로 호출하면 원본 함수가 실행된다. `original_function` 같은 속성은 **없다** |
| 속성 | `tool_name`, `tool_spec` |
| Tool 호출 내역 | `AgentResult.metrics.tool_metrics` — 툴 이름 → `call_count` / `success_count` |
| Tool 내부 예외 | 데코레이터가 잡아 error 상태의 ToolResult로 바꾼다. 따라서 인자 검증 실패가 Tool 실패로 기록된다 |
| MCP 의존성 | `mcp>=1.23.0`이 **핵심 의존성**이다. 별도 extra가 필요 없다 |
| MCP 클라이언트 | `from strands.tools.mcp import MCPClient`. `ToolProvider`이므로 `Agent(tools=[client])`로도 등록 가능 |
| MCP Tool 선별 | `tool_filters={"allowed": [...], "rejected": [...]}`, `prefix=` |
| MCP 장애 격리 | `continue_on_error=True`면 연결 실패 시 예외 대신 Tool 0개. `connection_failed` 속성으로 확인 |
| MCP Tool 직접 호출 | `call_tool_sync(tool_use_id, name, arguments)` → `MCPToolResult` (`status`, `content`, `isError`) |
| MCP 전송 | `MCPClient(url=...)`는 streamable HTTP, `MCPClient(lambda: stdio_client(...))`는 stdio |
| MCP 세션 | `start()` / `stop(exc_type, exc_val, exc_tb)` 또는 context manager |

### 3.2 Google Calendar MCP 서버

| 항목 | 값 |
| --- | --- |
| 서버 | 커뮤니티 프로젝트 `@cocal/google-calendar-mcp` (nspady/google-calendar-mcp), 고정 태그 `v2.6.3` |
| 런타임 | Node.js. **공개된 Docker 이미지가 없어 git 태그에서 직접 빌드한다** |
| 전송 | `TRANSPORT=http`, MCP endpoint는 루트 경로, health는 `/health`, 기본 포트 3000 |
| 노출 Tool | 12개. 이 프로젝트는 `list-events`·`create-event`·`update-event`·`delete-event` 4개만 사용한다 |
| 인증 | Google Cloud 프로젝트 + Calendar API 활성화 + OAuth 2.0 "Desktop app" 자격증명. 최초 동의는 브라우저 필요 |
| 자격증명 위치 | 컨테이너 `/app/gcp-oauth.keys.json` (저장소 `secrets/`에서 read-only 마운트, gitignore됨) |
| 토큰 저장 | 컨테이너 `/home/nodejs/.config/google-calendar-mcp`, Docker 볼륨 `calendar_tokens` |
| 비용 | Google Calendar API는 쿼터 기반 무료. 개인 사용 범위에서 현금 비용 없음 |

**아직 검증하지 않은 것:** 실제 OAuth 자격증명으로 컨테이너를 띄워 일정을 읽고 쓰는 경로는 미검증이다. 자격증명이 아직 없다. 단위 테스트는 기록된 MCP 응답 형태로 검증했다.

### 3.3 timeapi.io (현재 시각) — 2026-09-13 실호출 확인

| 항목 | 값 |
| --- | --- |
| Endpoint | `https://timeapi.io/api/Time/current/zone?timeZone=<IANA>` |
| 인증 | 불필요 |
| 응답 | `year`·`month`·`day`·`hour`·`minute`·`seconds`·`dayOfWeek`·`dstActive` 등. 응답 시간 약 1.3초 |
| 잘못된 입력 | HTTP 400과 `"Invalid Timezone"` |
| 사용 필드 | 정수 필드만 사용한다. `dateTime` 문자열은 소수점 7자리를 담아 파싱을 의존하지 않는다 |
| 요일 | API의 영어 `dayOfWeek`를 쓰지 않고 코드가 계산한다 |

- `worldtimeapi.org`는 **서비스 종료됐다.** 연결이 리셋된다 (2026-09-13 확인).
- `timeapi.world`는 조사한 경로에서 404였다.
- **무료 사용 한도가 문서에 공개되어 있지 않다.** 확인하지 못했다. 한도에 걸리면 로컬 시계 폴백으로 동작한다.

`zoneinfo`는 Windows에 IANA 시간대 DB가 없어 실패한다. 두 머신의 동작을 같게 하려고 `tzdata`를 의존성에 넣었다.

### 3.4 Open-Meteo

| 항목 | 값 |
| --- | --- |
| Forecast | `https://api.open-meteo.com/v1/forecast` — 비상업적 사용에 API key 불필요 (공식 문서 확인) |
| Geocoding | `https://geocoding-api.open-meteo.com/v1/search` — 도시명을 좌표로 변환 |
| 사용 변수 | `temperature_2m`, `relative_humidity_2m`, `precipitation`, `weather_code` |

**아직 검증하지 않은 것:** 실제 네트워크 호출은 미검증이다. 단위 테스트는 응답 샘플을 주입해 파싱만 검증했다.

## 4. 실행 환경

### 4.1 개발 머신 (Windows 데스크톱) — 실측 2026-09-10

| 항목 | 값 |
| --- | --- |
| OS | Windows 11 Pro 26200 |
| CPU | AMD Ryzen 5 3500X — 6코어 / **6스레드 (SMT 없음)**, 3.59GHz |
| RAM | 16GB 물리 (측정 시점 가용 1.66GB, Chrome·VS Code 점유) |
| GPU | NVIDIA GTX 1660 SUPER **6GB** (가용 4.98GB), 드라이버 591.86, CC 7.5 |
| Disk | C: 여유 201GB / D: 여유 255GB |
| Python | 3.12.7 (`C:\Python\python.exe`) |
| Docker | Docker Desktop 설치됨, **데몬 중지 상태** |
| WSL | WSL2 사용 가능, `docker-desktop` 배포판만 존재 (Ubuntu 없음) |
| uv | 0.12.13 (사용자 홈의 `.local/bin`). unit 테스트 실행용으로 설치함 |
| Ollama | **미설치** (의도적. 배포 대상이 아니므로 여기서 벤치마크하지 않는다) |

### 4.2 배포 대상 (Linux 미니PC) — 실측 2026-09-10

| 항목 | 값 |
| --- | --- |
| OS | Ubuntu 24.04.4 LTS, kernel 6.8.0-137-generic, x86_64 |
| CPU | Intel N150, 4코어 / 4스레드, 최대 3.6GHz, L3 6MiB |
| SIMD | AVX, AVX2, F16C, FMA 지원. AVX-512 미지원 |
| RAM | 15GiB 총량, 측정 시 MemAvailable 9GiB, swap 4GiB |
| Disk | 루트 볼륨 98GiB 중 48GiB 여유 |
| GPU/NPU | Intel Alder Lake-N 내장 GPU (`/dev/dri/card0`). NVIDIA/AMD GPU 및 NPU는 확인되지 않음 |
| 컨테이너 | Docker 29.1.3 및 Docker Compose v5.1.3, Docker 데몬 실행 확인 |
| 기본 도구 | Python 3.12.3, Git, curl. Ollama·Redis·PostgreSQL·pip3 미설치 |

N150은 CPU 추론을 기준으로 모델을 선정한다. 내장 GPU는 감지됐지만 범용 렌더 노드(`/dev/dri/renderD*`)가 확인되지 않았으므로 GPU/NPU 가속을 전제로 하지 않는다. RAM 및 디스크 용량상 2B~4B급 양자화 모델을 우선 벤치마크하고, 9B급은 첫 후보에서 제외한다.

**개발 머신의 벤치마크 결과를 미니PC에 이전하지 않는다.** 개발 머신에는 6GB GPU가 있고 이 미니PC의 가속 조건은 다르므로, 응답 속도와 실행 가능 모델 크기가 달라진다. 하드웨어와 무관한 품질 지표(라우팅 정확도, Tool Calling 성공률)만 이전 가능하다.


## 5. 런타임 구성

### 5.1 현재 구성

- API는 `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`으로 실행한다.
- Ollama는 Docker 컨테이너(`docker-compose.benchmark.yml`)로 실행 중이다.
- 캘린더 MCP 서버는 `docker compose -f docker-compose.calendar.yml up -d --build`로 실행한다. 포트는 loopback에만 연다.
- 캘린더 MCP 세션은 **프로세스 단위로 한 번** 열고 재사용한다 (`app/services/runtime.py`). 첫 요청에서 지연 생성되고 FastAPI 종료 시 닫힌다.
- `CALENDAR_MCP_URL`이 비어 있거나 연결이 실패하면 Schedule Agent는 Tool 없이 동작한다. 요청 자체는 실패하지 않는다.

### 5.2 목표 구성 (Phase 9, 아직 미구현)

Docker Compose 서비스: `assistant-api`(FastAPI + Strands), `ollama`, `calendar-mcp`, `redis`, `postgres`.
Docker 네트워크로 통신하고, PostgreSQL과 Ollama 모델 데이터에 볼륨을 적용한다. 미니PC 재부팅 후 자동 복구되도록 재시작 정책을 건다.

요청 처리 흐름:

```
User → FastAPI
     → Redis Session Memory 조회
     → 관련 Long-term Memory 조회
     → Orchestrator Agent → 전문 Agent 선택
     → Agent가 Tool 선택 → Tool 실행
     → 응답 생성
     → Redis Session Memory 저장
     → Memory Agent가 저장 후보 판단 → Application 검증 → PostgreSQL 저장
```

### 외부 브라우저 접근

- FastAPI는 `GET /`에서 같은 origin의 `POST /chat`을 호출하는 정적 채팅 화면을 제공한다. `/docs`는 계속 제공된다.
- 외부 hostname은 `personal-agent.changee.cloud`이며, Cloudflare Tunnel Public Hostname의 Service URL은 `http://127.0.0.1:8000`이어야 한다.
- 미니PC API는 `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`으로 loopback에만 바인딩한다.
- Cloudflare Access의 허용 정책, 인증된 외부 HTTPS 채팅 요청 및 미인증 접근 차단을 확인했다.

## 6. 컨벤션

- 문서 언어는 한국어. 코드 식별자와 커밋 타입은 영어.
- `.sh` 파일은 LF 개행 (`.gitattributes`가 강제).
- 정책·워크플로우 규칙의 소유자는 `CLAUDE.md` = `AGENTS.md`이며, 이 문서는 그것을 복제하지 않는다.
