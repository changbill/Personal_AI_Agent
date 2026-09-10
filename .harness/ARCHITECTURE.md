# ARCHITECTURE — 기술 스택·구조 현재 상태

> 이 문서는 **지금 어떤 상태인지**만 담는다. 왜 그렇게 정했는지는 `DECISIONS.md`, 진행 상황은 `STATE.md`가 소유한다.
> 아직 존재하지 않는 것은 "없음"으로 적는다. 있다고 가정해서 쓰지 않는다.

최종 갱신: 2026-09-10

## 1. 코드베이스 현황

**현재 애플리케이션 코드는 존재하지 않는다.** 저장소에 있는 것은 다음이 전부다.

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

없는 것: `pyproject.toml`, `uv.lock`, `app/`, `tests/`, `Dockerfile`, `docker-compose.yml`, `.env.example`.

## 2. 목표 디렉터리 구조 (아직 미생성)

```
app/
├── main.py
├── api/            chat.py
├── agents/         orchestrator.py, schedule_agent.py, search_agent.py,
│                   general_agent.py, memory_agent.py
├── tools/          calendar_tools.py, search_tools.py, weather_tools.py,
│                   memory_tools.py
├── memory/         session_memory.py, long_term_memory.py,
│                   memory_extractor.py, memory_retriever.py
├── repositories/   memory_repository.py
├── models/         memory.py
├── services/       orchestrator_service.py
└── core/           config.py, logging.py

tests/
├── agents/  tools/  memory/  evaluation/
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

**아직 실측하지 않은 것:** thinking 모드를 끄는 경로(`additional_args`로 `think=False` 전달이 실제로 먹는지)와 `options={"num_ctx": N}` 적용 여부. Phase 1에서 확인한다.

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
| uv | **미설치** |
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


## 5. 런타임 구성 (목표, 아직 미구현)

Docker Compose 4개 서비스: `assistant-api`(FastAPI + Strands), `ollama`, `redis`, `postgres`.
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

## 6. 컨벤션

- 문서 언어는 한국어. 코드 식별자와 커밋 타입은 영어.
- `.sh` 파일은 LF 개행 (`.gitattributes`가 강제).
- 정책·워크플로우 규칙의 소유자는 `CLAUDE.md` = `AGENTS.md`이며, 이 문서는 그것을 복제하지 않는다.
