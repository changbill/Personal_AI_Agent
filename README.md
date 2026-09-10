# Personal AI Agent

로컬 Ollama와 Strands Agents SDK를 사용하는 개인 비서입니다. 현재 Phase 1에서는 도구·메모리 없는 단일 General Agent와 `POST /chat`만 제공합니다.

## 개발 실행

Python 3.12와 uv가 필요합니다. Ollama 서버와 모델을 준비한 뒤 다음 환경변수를 설정합니다.

- `OLLAMA_HOST`: Ollama 서버 HTTP 주소
- `OLLAMA_MODEL`: `qwen3.5:2b-q4_K_M`
- `OLLAMA_NUM_CTX`: `2048`

서버는 `uv run uvicorn app.main:app --reload`로 실행합니다. 기본 검증은 `uv run pytest -m unit`입니다. Ollama 실호출 검증은 `uv run pytest -m llm`으로 별도 실행합니다.
