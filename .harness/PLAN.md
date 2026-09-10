# PLAN — 아직 안 끝난 계획

> 이 문서는 **안 끝난 것만** 담는다. 항목이 끝나면 여기서 제거하고 `STATE.md`에 Phase 한 줄로 반영한다.
> 완료 항목을 체크 표시만 남긴 채 방치하지 않는다.

최종 갱신: 2026-09-10

## Phase 0 — 환경 검증 (진행 중, 사용자 입력 대기)

### 0-A. 미니PC 실측 — **차단됨: 사용자 입력 필요**

- [ ] 미니PC에서 `scripts/phase0_probe.sh` 실행하고 출력 확보
- [ ] 결과를 `ARCHITECTURE.md` 4.2절에 기록
- [ ] MemAvailable과 AVX2 지원 여부로 실행 가능한 모델 크기 확정

측정해야 할 것: CPU 모델·코어 수, MemAvailable, **AVX/AVX2/AVX512 지원 여부**(CPU 추론 처리량을 크게 가른다), GPU/NPU 유무, Disk 여유, Docker 설치 여부.

### 0-B. Ollama 설치 및 모델 벤치마크 (0-A 이후)

- [ ] 미니PC에 Ollama 설치 (Docker vs 호스트 직접 설치를 자원 효율 기준으로 비교 후 결정)
- [ ] 후보 모델 pull 및 실행 가능 여부 확인
- [ ] 모델별 측정: 모델 로딩 가능 여부, RAM 사용량, 응답 속도(tok/s), 한국어 품질, Tool Calling 동작 여부, Structured Output 안정성
- [ ] 결과 비교 후 Phase 1에서 쓸 모델 태그 확정 → `DECISIONS.md`에 근거 기록

**모델 후보** (Ollama 라이브러리 실측 용량, 2026-09-10 확인)

| 후보 | 태그 | 용량 | 적합 조건 |
| --- | --- | --- | --- |
| A | `qwen3.5:2b-q4_K_M` | 1.9GB | RAM 4~8GB 미니PC 1순위 |
| B | `qwen3.5:4b-q4_K_M` | 3.4GB | RAM 8~16GB, 품질 우선 |
| C | `qwen2.5:3b` | ~1.9GB | thinking 없는 대조군 (지연시간 예측 가능) |
| D | `qwen3.5:0.8b` | 1.0GB | RAM 4GB 미만 최후수단 |
| E | `qwen3.5:9b-q4_K_M` | 6.6GB | RAM 16GB+ 여유 있을 때만 |

qwen3.5는 tools·thinking·vision을 지원하고 context 256K. qwen2.5는 tools만 지원하고 thinking 없음.
`qwen3.5:latest`는 9b를 가리키므로 **태그를 반드시 명시한다.**

## Phase 1 — 기본 Agent (미착수)

- [ ] `uv` 설치 및 `pyproject.toml` 초기화 (Python 3.12)
- [ ] 의존성 추가: `strands-agents[ollama]`, `fastapi`, `uvicorn`, dev로 `pytest`, `ruff`
- [ ] pytest 마커 등록 (`unit`, `integration`, `llm`)
- [ ] Ollama 연결 및 `OllamaModel` 구성
- [ ] **thinking 모드 비활성화 경로 실측 검증** — `additional_args`로 `think=False`가 실제로 전달되는지 확인하고 결과를 `ARCHITECTURE.md` 3절과 `CLAUDE.md` 로컬 LLM 정책에 반영
- [ ] **`options={"num_ctx": N}` 적용 확인** 및 초기값 결정 → `DECISIONS.md`
- [ ] 단일 Agent로 `POST /chat` 구현
- [ ] 응답 검증 테스트 작성 (`unit` + 최소한의 `llm`)

## Phase 2 이후 (미착수, 개요만)

- **Phase 2 Multi Agent** — Orchestrator / Schedule / Search / General 구현, 라우팅 테스트
- **Phase 3 Tool Calling** — 역할별 Tool 구현, Agent별 Tool 분리, Description 작성, 오선택 사례를 테스트로 축적
- **Phase 4 Session Memory** — Redis, TTL, multi-turn
- **Phase 5 Long-term Memory** — PostgreSQL, Memory Agent, 후보 추출, 저장 조건, 중복·충돌 처리
- **Phase 6 Memory Retrieval** — 검색, Context Injection, 선별, Recall 평가
- **Phase 7 Memory 고도화** — pgvector, Local Embedding, Semantic Retrieval. **필요성이 데이터로 확인된 경우에만 착수**
- **Phase 8 평가** — 테스트 데이터셋, 정확도·지연시간·CPU/RAM 측정, 변경 전후 비교
- **Phase 9 배포** — Dockerfile, Compose, Volume, Network, 환경변수, 재시작 정책, 재부팅 후 자동 복구 확인

## 미결정 사항 (해당 Phase에서 확정)

| 항목 | 확정 시점 |
| --- | --- |
| Ollama를 Docker로 띄울지 호스트에 직접 설치할지 | Phase 0-B |
| 사용할 모델 태그 | Phase 0-B |
| `num_ctx` 값 | Phase 1 |
| Redis TTL (24시간 또는 7일에서 시작) | Phase 4 |
| Session Memory에서 LLM에 넘길 최근 메시지 수 N | Phase 4 |
| ORM 사용 여부, 스키마 마이그레이션 도구 | Phase 5 |
| confidence threshold, allowed_types | Phase 5 |
| Context에 주입할 Memory 개수 상한 | Phase 6 |
| 타입 체크 도구 도입 여부 | 미정 |
