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
