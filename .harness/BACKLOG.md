# BACKLOG — 지금 하지 않지만 나중에 할 것

> 진행 중인 계획은 `PLAN.md`가 소유한다. 여기에는 착수 시점이 정해지지 않은 것만 둔다.
> 항목을 착수하기로 하면 `PLAN.md`로 옮기고 여기서 제거한다.

최종 갱신: 2026-09-10

## 기능

- **Agent 간 협업이 필요한 복합 요청.** 예: "비 오면 내일 약속 취소해줘"는 Search Agent와 Schedule Agent가 함께 필요하다. 현재 Orchestrator는 전문 Agent 하나를 고르는 설계이므로 범위 밖이다. Phase 2~3 평가에서 이런 요청의 빈도를 보고 판단한다.
- **추가 API.** `GET /sessions/{session_id}`, `GET /memories/{user_id}`, `DELETE /memories/{memory_id}`. Phase 1의 `POST /chat` 이후 필요해지면 착수한다.
- **Session Memory 요약.** 대화가 길어질 때 이전 대화를 요약해 토큰을 줄인다. Phase 4에서 최근 N개 방식으로 시작하고, N만으로 부족해지면 착수한다.
- **일정 데이터의 실제 출처.** 현재 Schedule Agent의 Tool은 자체 DB를 가정한다. 외부 캘린더(Google Calendar 등) 연동은 무료 사용 범위를 확인한 뒤 별도로 판단한다.

## 운영·인프라

- **미니PC 전력 사용량 측정.** 계획상 전력·CPU·RAM도 운영 비용으로 본다. 측정 방법이 아직 없다.
- **CI 구성.** 현재 없다. 최소한 `unit` 테스트와 `scripts/check_docs_sync.sh`를 돌리는 워크플로가 있으면 좋다.
- **타입 체크 도구 도입 여부.** ruff만 쓰고 있다. 코드가 쌓인 뒤 필요성을 재평가한다.
- **`scripts/check_docs_sync.sh`를 pre-commit 훅으로 연결.** 지금은 수동 실행이라 잊을 수 있다.

## 문서

- **README.md가 스텁이다.** 제목 한 줄뿐. 저장소 진입점 역할(개요, 실행 방법, 커밋 컨벤션 안내)을 하도록 채워야 한다. 실행 방법은 Phase 1에서 실제로 실행 가능해진 뒤에 쓰는 것이 맞다.

## 검증 필요 (추측으로 구현하지 말 것)

- **Strands `OllamaModel`에서 thinking 모드를 끄는 정확한 경로.** `additional_args`에 `think=False`를 넣는 방식이 실제로 Ollama API까지 전달되는지 미확인. Phase 1에서 확인한다.
- **Strands에서 `options={"num_ctx": N}`가 실제로 적용되는지.** 미확인.
- **Ollama를 Docker로 띄울 때와 호스트에 직접 설치할 때의 미니PC 자원 차이.** 미측정.
