# STATE — 완료된 것의 Phase 단위 스냅샷

> 이 문서는 **끝난 것만** 담는다. 세션별 서술은 `HANDOFF.md`, 아직 안 끝난 계획은 `PLAN.md`, 결정 이유는 `DECISIONS.md`가 소유한다.
> Phase가 끝나면 그 Phase를 한 줄로 갱신한다. 이슈를 하나하나 로그처럼 쌓지 않는다.

최종 갱신: 2026-09-12

| Phase | 상태 | 요약 |
| --- | --- | --- |
| 0. 환경 검증 | 완료 | Docker CPU Ollama에서 `qwen3.5:2b-q4_K_M`를 기본 모델로 선정. 3회 평균 4.20 tok/s, Tool Calling·JSON 출력 확인. |
| 1. 기본 Agent | 완료 | 단일 General Agent 기반 `POST /chat`·브라우저용 `GET /`, `.env` 자동 로드 환경변수 설정, 구조화 로그, unit·llm 검증 및 Cloudflare Access 외부 접근 확인 완료. |
| 2. Multi Agent | 완료 | 규칙 기반 Orchestrator가 Schedule/Search/General 중 하나를 선택하고, 안전 폴백·API 위임·회귀 unit 테스트를 갖춤 |
| 3. Tool Calling | 미착수 | — |
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
