# DOMAIN — Agent·Tool·Memory 판정 규칙 현재 상태

> 이 문서는 **판정 규칙의 현재 상태**만 담는다. 구현 진행 상황은 `STATE.md`, 결정 이유는 `DECISIONS.md`가 소유한다.
> 여기 적힌 규칙은 프롬프트·Tool Description·검증 코드·평가 데이터셋의 기준이 된다. 넷 중 하나를 바꾸면 나머지도 같은 작업에서 맞춘다.

최종 갱신: 2026-09-12
구현 상태: **Phase 2 Agent 라우팅과 Phase 3-A Tool Calling 구현 완료.** Memory 관련 규칙(3절 이하)은 아직 미구현이다.

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

| Agent | Tool | 구현 상태 |
| --- | --- | --- |
| Schedule Agent | `get_schedule`, `create_schedule`, `update_schedule`, `delete_schedule` | Phase 3-A 구현 완료 |
| Search Agent | `get_weather` | Phase 3-A 구현 완료 |
| General Agent | `get_current_time` | Phase 3-A 구현 완료 |
| Search Agent | `search_web`, `search_place` | 미구현. 무료 제공자 결정 후 Phase 3-B |
| Memory (Agent/Application) | `search_memory`, `save_memory`, `update_memory` | 미구현. Phase 5~6 |
| General Agent | 일정·날씨·검색 Tool 없음 | 의도적으로 비워 둔다. `get_current_time`만 예외 |

각 Tool에는 역할·입력 파라미터·반환값·**호출해야 하는 상황**·**호출하면 안 되는 상황**을 명시한다. Description은 짧고 명확하게 유지한다.

### 2.1 Tool Description은 이 저장소가 소유한다

일정 Tool은 Google Calendar MCP 서버가 노출하는 Tool을 그대로 쓰지 않고, 자체 `@tool` 래퍼로 감싼다. MCP 서버의 Description은 편집할 수 없는 영어 한 줄이고 비호출 조건이 없어, 위 규칙을 코드에서 지킬 수 없기 때문이다. 소형 모델에서는 Description이 곧 Tool 선택 로직이다.

따라서 Tool 이름도 MCP 이름(`list-events` 등)이 아니라 이 표의 이름을 쓴다. 래퍼와 MCP Tool의 대응은 다음과 같다.

| 이 저장소의 Tool | MCP 서버 Tool |
| --- | --- |
| `get_schedule` | `list-events` |
| `create_schedule` | `create-event` |
| `update_schedule` | `update-event` |
| `delete_schedule` | `delete-event` |

MCP 서버가 노출하는 나머지 8개 Tool은 `tool_filters`로 차단하고, Application도 이 4개 외의 이름은 호출을 거부한다.

### 2.2 일정 Tool 계약

`get_schedule`

- 역할: 지정된 기간의 사용자 일정을 조회한다.
- 입력: `start_date`, `end_date` (둘 다 `YYYY-MM-DD`)
- Use when: 특정 날짜나 기간의 일정을 요청받았을 때 / 새 일정 생성 전 충돌을 확인할 때
- Do not use when: 일정을 만들거나 바꾸거나 지울 때 / 일정과 무관한 요청

`create_schedule`

- 역할: 새 일정을 추가한다.
- 입력: `summary`, `start_datetime`, `end_datetime` (필수), `description`, `location` (선택)
- Use when: 사용자가 약속이나 회의를 새로 잡아 달라고 할 때
- Do not use when: 기존 일정을 조회·변경할 때 / 제목이나 시작·종료 시각을 아직 모를 때

`update_schedule`

- 역할: 기존 일정의 내용을 바꾼다.
- 입력: `event_id` (필수), `summary`, `start_datetime`, `end_datetime`, `location` (선택)
- Use when: 기존 일정의 시각·제목·장소를 바꿔 달라고 하고 `event_id`를 알고 있을 때
- Do not use when: `event_id`를 모를 때 (먼저 `get_schedule`) / 새 일정을 만들 때 / 일정을 지울 때

`delete_schedule`

- 역할: 일정을 삭제한다.
- 입력: `event_id` (필수)
- Use when: 특정 일정을 취소·삭제해 달라고 하고 `event_id`를 알고 있을 때
- Do not use when: `event_id`를 모를 때 (먼저 `get_schedule`) / 내용만 바꾸면 되는 때

`get_weather`

- 역할: 지정한 도시의 현재 날씨를 조회한다.
- 입력: `city`
- Use when: 특정 지역의 날씨·기온·강수를 물어볼 때
- Do not use when: 과거나 여러 날 뒤의 예보를 물어볼 때 / 날씨와 무관한 검색 요청

**지명 해석은 코드가 판정한다.** Open-Meteo Geocoding의 색인은 로마자이므로 `language=ko`를 줘도
한국어 이름으로는 검색되지 않는다. 판정 순서는 다음과 같다.

| 순서 | 규칙 |
| --- | --- |
| 1 | 공백을 제거하고 `app/services/place_directory.py`의 한국 지명 표에서 찾는다 |
| 2 | 못 찾으면 `특별시`·`광역시`·`시`·`군`·`구`·`도` 등 접미사를 떼고 다시 찾는다. 접미사를 뗀 결과가 표에 있을 때만 뗀다 (`대구`를 `대`로 자르지 않기 위함) |
| 3 | `도` 단위 질의는 도청 소재 도시로 해석하고, 답변에 그 도시 이름을 남긴다 |
| 4 | 표에 없으면 Geocoding API를 부른다. 질의에 한글이 있으면 `country_code == "KR"` 결과를 우선한다 |
| 5 | 그래도 못 찾으면 Tool을 실패시킨다. 모델이 임의의 지역 날씨를 답하게 두지 않는다 |

표에 담는 범위는 17개 시·도와 주요 시까지다. 읍·면·동 단위는 Geocoding 폴백이 담당한다.

`get_current_time`

- 역할: 지금의 날짜·요일·시각을 조회한다. 등록 대상은 **General Agent뿐이다.**
- 입력: 없음
- Use when: 현재 날짜나 시각, 오늘이 무슨 요일인지 물어볼 때
- Do not use when: 일정을 조회·변경할 때 / 날씨를 물어볼 때 / 날짜와 무관한 일반 대화

### 2.3 Tool 인자 검증은 Application이 한다

LLM이 제안한 Tool 인자를 그대로 외부 시스템에 넘기지 않는다. 다음은 코드가 판정하며, 위반은 Tool 실패로 반환해 모델이 다시 시도하게 한다.

| 규칙 | 값 |
| --- | --- |
| 날짜 형식 | `start_date`·`end_date`는 `YYYY-MM-DD`만 허용. 시각이 붙으면 거부 |
| 날짜시간 형식 | `start_datetime`·`end_datetime`은 ISO 8601이며 시각을 포함해야 한다 |
| 기간 순서 | `end_date >= start_date`, `end_datetime > start_datetime` |
| 조회 기간 상한 | 최대 31일. Context에 들어갈 일정 수를 제한하기 위한 값 |
| 일정 길이 상한 | 최대 30일 |
| 부분 수정 | 시각을 바꾸려면 시작·종료를 함께 주어야 한다. 변경 항목이 하나도 없으면 거부 |
| 필수 식별자 | `update_schedule`·`delete_schedule`은 `event_id`가 비어 있으면 거부 |
| 허용 MCP Tool | 위 4개 외의 MCP Tool 이름은 호출하지 않는다 |

### 2.4 날짜는 Agent마다 다른 경로로 전달한다

"내일", "다음 주" 같은 상대 표현을 모델이 날짜로 바꾸려면 오늘 날짜를 알아야 한다. 전달 경로는 Agent마다 다르고, 기준은 **왕복 비용**이다.

| Agent | 날짜 전달 경로 | 이유 |
| --- | --- | --- |
| Schedule Agent | system prompt 주입 | 일정 요청은 항상 날짜가 필요하다. Tool로 받으면 조회 한 번에 왕복이 둘(시간 → 일정)이 되어 2B 모델에서 약 15초가 더 붙는다 |
| Search Agent | system prompt 주입 | 같은 이유 |
| General Agent | `get_current_time` Tool | 대화 대부분은 날짜가 필요 없다. 항상 주입하면 매 요청 Context를 낭비하고, 주입한 날짜를 그대로 읽으면 Tool이 무의미해진다 |

주입되는 날짜는 **`AGENT_TIMEZONE`에서 계산한다.** `date.today()`는 OS 로컬 시간대를 따르므로, 호스트가 UTC면 한국 시간 자정부터 오전 9시까지 날짜가 하루 밀린다. 이 구간은 실측으로 확인했다.

MCP 서버의 `get-current-time` Tool은 등록하지 않는다. Schedule Agent의 Tool 수를 늘리고, 우리가 Description을 소유하지 못한다.

### 2.5 시간 조회는 실패하지 않는다

`get_current_time`의 주 소스는 외부 API이고, 실패하면 `AGENT_TIMEZONE` 기준 로컬 시계로 폴백한다. 어느 소스를 썼는지 로그에 남긴다. 시간 조회가 요청 실패의 원인이 되면 안 된다.

### 2.6 Tool이 없을 때의 동작

캘린더 MCP 서버에 연결되지 않으면 Schedule Agent에 Tool을 **0개** 등록하고, system prompt가 연결되지 않았음을 알린다. 동작하지 않는 Tool을 등록해 두면 모델이 가져오지 않은 결과를 사실처럼 말하게 된다. 캘린더 부재는 요청 실패가 아니라 답변의 품질 저하로 처리한다.

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
