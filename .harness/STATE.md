# STATE — 완료된 것의 Phase 단위 스냅샷

> 이 문서는 **끝난 것만** 담는다. 세션별 서술은 `HANDOFF.md`, 아직 안 끝난 계획은 `PLAN.md`, 결정 이유는 `DECISIONS.md`가 소유한다.
> Phase가 끝나면 그 Phase를 한 줄로 갱신한다. 이슈를 하나하나 로그처럼 쌓지 않는다.

최종 갱신: 2026-09-10

| Phase | 상태 | 요약 |
| --- | --- | --- |
| 0. 환경 검증 | 진행 중 | 개발 머신 사양·툴체인 확인 완료, Strands/Ollama 사양 확인 완료. **미니PC 실측과 모델 벤치마크가 남아 있어 미완료.** |
| 1. 기본 Agent | 미착수 | — |
| 2. Multi Agent | 미착수 | — |
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
- `CLAUDE.md` / `AGENTS.md`를 이 프로젝트(Python) 기준으로 재작성하고 `scripts/check_docs_sync.sh`로 동기화 검증 자동화
- `.harness/` 문서 체계 신설
