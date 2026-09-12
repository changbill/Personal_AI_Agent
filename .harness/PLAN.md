# PLAN — 아직 안 끝난 계획

> 이 문서는 **안 끝난 것만** 담는다. 항목이 끝나면 여기서 제거하고 `STATE.md`에 Phase 한 줄로 반영한다.
> 완료 항목을 체크 표시만 남긴 채 방치하지 않는다.

최종 갱신: 2026-09-13

## Phase 3-A 남은 작업 — 실연동 검증 (확정, 사용자 작업 대기)

코드와 unit 테스트는 끝났다. 남은 것은 **실제 Google Calendar 연동 검증**이며, 사용자만 할 수 있는 단계가 앞에 있다.

### 사용자가 해야 하는 일

1. Google Cloud 프로젝트를 만들고 Google Calendar API를 활성화한다.
2. OAuth 2.0 클라이언트 ID를 application type **Desktop app**으로 발급하고 JSON을 내려받는다.
3. 저장소 루트에 `secrets/gcp-oauth.keys.json`으로 저장한다. `secrets/`는 gitignore되어 있다.
4. 미니PC에서 `docker compose -f docker-compose.calendar.yml up -d --build`를 실행한다.
   공개 이미지가 없어 첫 실행에서 Node 이미지 빌드가 일어난다.
5. 최초 OAuth 동의를 승인한다. 브라우저가 필요하고 미니PC는 loopback 전용이므로,
   SSH 포트 포워딩(`ssh -L 3000:127.0.0.1:3000 -L 3500:127.0.0.1:3500 ...`)으로 데스크톱 브라우저에서 승인한다.
6. 미니PC `.env`에 `CALENDAR_MCP_URL`을 넣는다. API와 MCP 서버가 같은 호스트면 `http://127.0.0.1:3000`이다.

### 그 다음 검증할 것

- [ ] `curl http://127.0.0.1:3000/health`로 MCP 서버 기동 확인
- [ ] API 로그에 `calendar_mcp_connected`가 남는지 확인
- [ ] `uv run pytest -m llm` 실행 — 일정 조회 Tool과 날씨 Tool을 실제 모델이 호출하는지 확인
- [ ] `POST /chat`으로 "내일 일정 알려줘" 호출 후 로그의 `tools_used`에 `get_schedule`이 남는지 확인
- [ ] 일정 생성·수정·삭제를 실제 캘린더에서 한 번씩 확인 (테스트용 캘린더 권장)
- [ ] 오선택 사례가 나오면 회귀 테스트로 남기고 Tool Description을 고친 뒤 `-m llm`을 다시 돌린다
- [ ] General Agent가 "오늘 며칠이야"에 `get_current_time`을 호출하고, 무관한 대화에서는 호출하지 않는지 확인
      (`-m llm`의 시간 Tool 테스트 2개가 이것을 검사한다)
- [ ] 미니PC의 OS 시간대를 확인한다. UTC라면 이번에 고친 날짜 계산이 실제로 차이를 만든다
      (`timedatectl`로 확인. 코드는 이제 `AGENT_TIMEZONE`을 따르므로 OS 설정과 무관하게 맞다)

### 미검증으로 남아 있는 것 (확인한 것처럼 서술하지 말 것)

- 실제 OAuth 자격증명으로 캘린더를 읽고 쓰는 경로. 단위 테스트는 기록된 MCP 응답 형태로만 검증했다
- 2B 모델이 Tool 4개 중에서 올바른 것을 고르는 비율. 측정하지 않았다
- 캘린더 MCP 컨테이너가 미니PC에서 차지하는 실제 RAM·CPU. 상한은 512M / 1.0 CPU로 걸어 두었으나 실측하지 않았다

## Phase 3-B — 웹·장소 검색 (제공자 결정 필요)

`search_web`과 `search_place`는 무료 제공자 선택이 선행되어야 한다. 조사 결과:

- Brave Search API 무료 tier는 2026년 2월에 폐지되고 월 $5 크레딧 과금제로 바뀌었다. 가입 시 카드가 필요하다
- Tavily·Firecrawl·SerpApi 등은 카드 없이 무료 tier를 제공하지만 계정과 키가 필요하고 월 쿼터가 낮다
- SearXNG 자체 호스팅은 현금 비용이 0이지만 미니PC RAM·CPU를 상시 점유한다 (현재 MemAvailable 9GiB)
- 장소 검색은 Kakao Local API가 무료 키로 사용 가능한지 아직 확인하지 않았다

선택 근거는 `DECISIONS.md`에 남긴다.

## 이후 Phase

- **Phase 4 Session Memory** — Redis, TTL, multi-turn
- **Phase 5 Long-term Memory** — PostgreSQL, Memory Agent, 후보 추출, 저장 조건, 중복·충돌 처리
- **Phase 6 Memory Retrieval** — 검색, Context Injection, 선별, Recall 평가
- **Phase 7 Memory 고도화** — pgvector, Local Embedding, Semantic Retrieval. **필요성이 데이터로 확인된 경우에만 착수**
- **Phase 8 평가** — 테스트 데이터셋, 라우팅·Tool 선택 정확도, 지연시간·CPU/RAM 측정, 변경 전후 비교
- **Phase 9 배포** — Dockerfile, 통합 Compose(캘린더 MCP 포함), Volume, Network, 환경변수, 재시작 정책, 재부팅 후 자동 복구 확인

## 미결정 사항 (해당 Phase에서 확정)

| 항목 | 확정 시점 |
| --- | --- |
| `search_web`·`search_place` 제공자 | Phase 3-B |
| Redis TTL (24시간 또는 7일에서 시작) | Phase 4 |
| Session Memory에서 LLM에 넘길 최근 메시지 수 N | Phase 4 |
| ORM 사용 여부, 스키마 마이그레이션 도구 | Phase 5 |
| confidence threshold, allowed_types | Phase 5 |
| Context에 주입할 Memory 개수 상한 | Phase 6 |
| 타입 체크 도구 도입 여부 | 미정 |
