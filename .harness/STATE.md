# STATE — 완료된 것의 Phase 단위 스냅샷

> 이 문서는 **끝난 것만** 담는다. 세션별 서술은 `HANDOFF.md`, 아직 안 끝난 계획은 `PLAN.md`, 결정 이유는 `DECISIONS.md`가 소유한다.
> Phase가 끝나면 그 Phase를 한 줄로 갱신한다. 이슈를 하나하나 로그처럼 쌓지 않는다.

최종 갱신: 2026-09-12

| Phase | 상태 | 요약 |
| --- | --- | --- |
| 0. 환경 검증 | 완료 | Docker CPU Ollama에서 `qwen3.5:2b-q4_K_M`를 기본 모델로 선정. 3회 평균 4.20 tok/s, Tool Calling·JSON 출력 확인. |
| 1. 기본 Agent | 완료 | 단일 General Agent 기반 `POST /chat`·브라우저용 `GET /`, `.env` 자동 로드 환경변수 설정, 구조화 로그, unit·llm 검증 및 Cloudflare Access 외부 접근 확인 완료. |
| 2. Multi Agent | 완료 | 규칙 기반 Orchestrator가 Schedule/Search/General 중 하나를 선택하고, 안전 폴백·API 위임·회귀 unit 테스트를 갖춤 |
| 3. Tool Calling | 3-A 구현 완료 (실연동 미검증), 3-B 미착수 | Google Calendar MCP 게이트웨이와 일정 Tool 4개, Open-Meteo `get_weather`, Agent Tool 사용 내역 로깅을 구현. General Agent에 `get_current_time`(timeapi.io + 로컬 폴백). 한국어 지명은 코드 소유 좌표 표가 해석하고 Geocoding은 폴백. Tool Description·이름은 자체 `@tool` 래퍼가 소유. unit 135개 통과, Open-Meteo 실호출 검증 완료. **실제 OAuth 연동과 `-m llm` 실행은 미검증.** `search_web`·`search_place`는 무료 제공자 미결정으로 3-B 대기 |
| 4. Session Memory | 미착수 | — |
| 5. Long-term Memory | 미착수 | — |
| 6. Memory Retrieval | 미착수 | — |
| 7. Memory 고도화 (조건부) | 미착수 | 필요성이 데이터로 확인되기 전까지 착수하지 않는다 |
| 8. 평가 | 미착수 | — |
| 9. 미니PC 배포 | 미착수 | — |

## Phase 0에서 지금까지 끝난 것

- 개발 머신(Windows 데스크톱) 사양과 설치된 툴체인 확인 — 상세는 `ARCHITECTURE.md`
- `strands-agents` 1.54.0의 Ollama 연동 사양 확인 (extra 이름, `OllamaModel` 파라미터, Python 요구 버전) — 상세는 `ARCHITECTURE.md`
- Ollama 라이브러리의 현재 Qwen 라인업과 소형 태그별 용량 확인 — 후보 목록은 `PLAN.md`
- `scripts/phase0_probe.sh` 작성 — 미니PC 사양 측정용, 읽기 전용
- 미니PC 실측 완료 — Intel N150(4코어, AVX2), RAM 15GiB(측정 시 MemAvailable 9GiB), 디스크 여유 48GiB, Intel 내장 GPU, Docker/Compose 실행 가능. 상세는 `ARCHITECTURE.md`
- `CLAUDE.md` / `AGENTS.md`를 이 프로젝트(Python) 기준으로 재작성하고 `scripts/check_docs_sync.sh`로 동기화 검증 자동화
- `.harness/` 문서 체계 신설
## Phase 1에서 지금까지 끝난 것

- FastAPI `POST /chat`, 단일 General Agent, 환경변수 기반 Ollama 설정, 원문을 남기지 않는 구조화 요청 로그 구현
- `think=false`와 `num_ctx=2048`의 Strands→Ollama 전달 경로를 패키지 코드 및 미니PC 실제 호출로 확인
- `ruff check`, unit 4개, 실제 Ollama llm 테스트 1개 통과

## Phase 2에서 끝난 것

- 규칙 기반 Orchestrator, Schedule/Search/General 단일 선택, 복합·무효 선택의 General 폴백
- 선택 결과를 구조화 로그에 남기는 API 위임과 회귀 unit 테스트

## Phase 3-A에서 지금까지 끝난 것

- `strands-agents` 1.54.0의 Tool·MCP 사양을 sdist 코드로 확인 (상세는 `ARCHITECTURE.md` 3.1절)
- 캘린더 MCP 게이트웨이 — 4개 Tool 허용 목록, 연결 실패 격리, 프로세스 단위 세션, 종료 시 정리
- 일정 Tool 4개와 Open-Meteo `get_weather` — Description·이름을 자체 `@tool` 래퍼가 소유
- 한국 17개 시·도와 주요 시의 지명→좌표 표(`app/services/place_directory.py`). 접미사·도 단위 해석, 한글 질의의 KR 우선 폴백 (상세는 `DOMAIN.md` 2.2절)
- Open-Meteo 실호출 검증 완료 — 서울·부산·대전·제주도·경기도·인천·도쿄·Paris 조회와 미확인 지명의 실패 처리
- 일정 입력 검증 계층 — 날짜 형식, 기간 순서, 조회·길이 상한, 부분 수정 규칙 (상세는 `DOMAIN.md` 2.3절)
- 오늘 날짜·요일·시간대를 `AGENT_TIMEZONE` 기준으로 코드가 계산해 system prompt에 주입
- `get_current_time` Tool과 시간 서비스 — timeapi.io 주 소스, 로컬 시계 폴백, 사용한 소스를 로깅
- `date.today()`가 OS 시간대를 따라 UTC 호스트에서 날짜가 하루 밀리던 결함 수정. `tzdata` 추가, `AGENT_TIMEZONE` 기동 검증
- JSON fetcher를 `app/services/http_client.py`로 분리해 날씨·시간 서비스가 공유
- Agent 반환 계약을 `AgentReply(text, tool_calls)`로 교체하고 `tools_used`·`tools_failed`를 실제 값으로 로깅
- `docker-compose.calendar.yml`, `.env.example`, `.gitignore` 비밀값 경로 추가
- 개발 머신에 uv 0.12.13 설치. `ruff format`·`ruff check` 통과, unit 100개 통과
