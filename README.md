# Personal AI Agent

로컬 Ollama와 Strands Agents SDK를 사용하는 개인 비서입니다. 현재는 도구·메모리 없는 단일 General Agent, `POST /chat`, 브라우저용 `GET /`를 제공합니다.

## 개발 실행

Python 3.12와 uv가 필요합니다. Ollama 서버와 모델을 준비한 뒤 다음 환경변수를 설정합니다.

- `OLLAMA_HOST`: Ollama 서버 HTTP 주소
- `OLLAMA_MODEL`: `qwen3.5:2b-q4_K_M`
- `OLLAMA_NUM_CTX`: `2048`

개발 서버는 다음 명령으로 실행합니다.

```sh
uv run uvicorn app.main:app --reload
```

기본 검증은 `uv run pytest -m unit`입니다. Ollama 실호출 검증은 `uv run pytest -m llm`으로 별도 실행합니다.

## 외부 브라우저 접근

`https://personal-agent.changee.cloud`은 Cloudflare Tunnel의 Public Hostname으로 사용합니다. API는 공인 IP나 포트 포워딩으로 노출하지 않습니다.

미니PC에서 API를 loopback에만 바인딩합니다.

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Cloudflare Dashboard에서 다음을 확인합니다.

- Tunnel Public Hostname: `personal-agent.changee.cloud`
- Service URL: `http://127.0.0.1:8000`
- Cloudflare Access Application: 허용한 이메일 또는 IdP 그룹만 통과

Tunnel token과 실제 credential은 저장소, `.env.example`, 대화에 기록하지 않습니다. Access 인증을 적용하기 전에는 이 도메인을 공개 서비스로 사용하지 마세요.
