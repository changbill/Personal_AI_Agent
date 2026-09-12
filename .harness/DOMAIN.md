# DOMAIN — Agent·Tool·Memory 판정 규칙 현재 상태

> 이 문서는 **판정 규칙의 현재 상태**만 담는다. 구현 진행 상황은 `STATE.md`, 결정 이유는 `DECISIONS.md`가 소유한다.
> 여기 적힌 규칙은 프롬프트·Tool Description·검증 코드·평가 데이터셋의 기준이 된다. 넷 중 하나를 바꾸면 나머지도 같은 작업에서 맞춘다.

최종 갱신: 2026-09-12
구현 상태: **Phase 2 Agent 라우팅 구현 완료.** Tool Calling과 Memory 관련 규칙은 아직 미구현이다.

## 1. Agent 라우팅 규칙

Orchestrator는 사용자 의도를 분석해 전문 Agent 하나를 고른다. **Orchestrator는 직접 Tool을 실행하지 않는다.** Phase 2 구현은 비용과 지연을 줄이기 위해 일정·실시간 정보의 명확한 신호를 코드 규칙으로 판정하며, Schedule과 Search 신호가 함께 있거나 허용되지 않은 선택값이면 General Agent로 폴백한다.

| Agent | 담당 | 라우팅 기준 |
| --- | --- | --- |
| Schedule Agent | 일정 조회·생성·수정·삭제·충돌 확인 | 요청이 사용자의 일정(시간이 잡힌 약속)을 읽거나 바꾸려 할 때 |
| Search Agent | 웹 검색, 날씨, 장소 | 답하려면 **외부 실시간 정보**가 필요할 때 |
| General Agent | 일반 대화 | 전문 Agent도 Tool도 필요 없을 때. 필요하면 Long-term Memory를 반영한다 |
| Memory Agent | 장기 저장 후보 추출 | 사용자 요청에 대한 응답 경로가 아니라, **응답 생성 이후** 후처리로 동작한다 |

예시

| 입력 | 기대 Agent |
| --- | --- |
| "내일 일정 알려줘" | Schedule Agent |
| "오늘 인천 날씨 알려줘" | Search Agent |
| "내가 평일에 몇 시 이후 약속을 선호했지?" | General Agent + Long-term Memory 조회 |

경계 규칙

- 일정을 **만들기 전에** 충돌을 확인해야 하면 Schedule Agent 안에서 조회 후 생성한다. 두 Agent로 쪼개지 않는다.
- 외부 정보와 일정이 함께 필요한 요청(예: "비 오면 약속 취소")은 현재 설계 범위 밖이다. `BACKLOG.md` 참조.

## 2. Tool 목록과 호출 조건

**Agent마다 자기 역할에 필요한 Tool만 등록한다.** 소형 로컬 모델은 선택지가 늘수록 오선택이 급증한다.

| Agent | Tool |
| --- | --- |
| Schedule Agent | `get_schedule`, `create_schedule`, `update_schedule`, `delete_schedule` |
| Search Agent | `search_web`, `get_weather`, `search_place` |
| Memory (Agent/Application) | `search_memory`, `save_memory`, `update_memory` |
| General Agent | 없음 |

각 Tool에는 역할·입력 파라미터·반환값·**호출해야 하는 상황**·**호출하면 안 되는 상황**을 명시한다. Description은 짧고 명확하게 유지한다.

`get_schedule` 예시

- 역할: 지정된 기간의 사용자 일정을 조회한다.
- Use when: 특정 날짜의 일정을 요청받았을 때 / 새 일정 생성 전 충돌을 확인할 때
- Do not use when: 일정과 관련 없는 요청 / 실제 일정 생성 작업

## 3. Long-term Memory 저장 판정

### 3.1 역할 분리 (이 경계를 흐리지 않는다)

| 주체 | 책임 |
| --- | --- |
| Memory Agent (LLM) | 후보 추출, 저장 필요성 **판단**, memory_type 분류, Structured Output 생성 |
| Application (코드) | 결과 **검증**, confidence 확인, 중복 검사, 기존 Memory와 충돌 검사, INSERT/UPDATE 최종 결정 |

**LLM은 저장을 결정하지 않는다.** 최종 결정은 항상 Application이 내린다.

### 3.2 저장 후보 판단 기준

1. 이후 세션에서도 활용할 가능성이 있는가?
2. 일정 기간 지속되는 정보인가?
3. 사용자 선호·습관·반복 패턴·주요 정보인가?
4. 일회성 정보가 아닌가?
5. 기존 Memory와 중복되거나 충돌하지 않는가?

| 발화 | 저장 | 이유 |
| --- | --- | --- |
| "평일 약속은 오후 7시 이후를 선호해" | O | 반복 활용되는 선호 |
| "아이스 아메리카노를 좋아해" | O | 지속되는 선호 |
| "오늘 오후 3시에 병원 가" | X | 일회성 사실. 일정은 Schedule의 몫 |

### 3.3 Structured Output 형태

```json
{
  "should_store": true,
  "memory_type": "preference",
  "key": "weekday_meeting_time",
  "value": "19:00 이후",
  "confidence": 0.93,
  "reason": "향후 일정 관리에서 반복적으로 활용할 수 있는 사용자 선호"
}
```

### 3.4 Application 검증 조건

```
should_store == true
AND confidence >= threshold
AND memory_type in allowed_types
```

`threshold`와 `allowed_types`의 확정값은 아직 정하지 않았다. Phase 5에서 정하고 근거를 `DECISIONS.md`에 남긴다.

## 4. 중복·충돌 처리

기존 `coffee_preference = iced americano` 상태에서 "요즘은 커피를 마시지 않아"가 들어온 경우:

```
Memory Candidate 생성
→ 관련 기존 Memory 조회
→ 중복 여부 판단
→ 충돌 여부 판단
→ 새로운 정보면 INSERT
→ 기존 정보가 변경된 것이면 UPDATE
```

**충돌 시 기존 값을 조용히 덮어쓰지 않는다.** 같은 `key`에 대한 변경은 UPDATE로 처리하고 `updated_at`을 갱신한다.

## 5. Memory 레코드 필드

`id`, `user_id`, `memory_type`, `key`, `value`, `confidence`, `created_at`, `updated_at`, `last_accessed_at`

## 6. Retrieval 규칙

- **모든 Memory를 프롬프트에 넣지 않는다.** 현재 요청과 관련된 것만 선별해 주입한다.
- 초기 검색은 `memory_type` / `key` 기반이다. 자연어(의미) 검색은 필요성이 평가로 확인되기 전까지 도입하지 않는다.
- Context에 들어가는 Memory 개수에 상한을 둔다. 확정값은 Phase 6에서 정한다.
