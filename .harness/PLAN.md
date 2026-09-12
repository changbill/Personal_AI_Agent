# PLAN — 아직 안 끝난 계획

> 이 문서는 **안 끝난 것만** 담는다. 항목이 끝나면 여기서 제거하고 `STATE.md`에 Phase 한 줄로 반영한다.
> 완료 항목을 체크 표시만 남긴 채 방치하지 않는다.

최종 갱신: 2026-09-12


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
| Redis TTL (24시간 또는 7일에서 시작) | Phase 4 |
| Session Memory에서 LLM에 넘길 최근 메시지 수 N | Phase 4 |
| ORM 사용 여부, 스키마 마이그레이션 도구 | Phase 5 |
| confidence threshold, allowed_types | Phase 5 |
| Context에 주입할 Memory 개수 상한 | Phase 6 |
| 타입 체크 도구 도입 여부 | 미정 |
