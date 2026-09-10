# Phase 0-B Ollama 모델 벤치마크

측정일: 2026-09-10
대상: Intel N150 (4코어, AVX2), RAM 15GiB, Ubuntu 24.04.4 LTS
Ollama: Docker CPU 컨테이너, Ollama 0.33.3
공통 설정: `num_ctx=2048`, `num_predict=96`, `temperature=0`, `think=false`, 62개 출력 토큰의 한국어 고정 프롬프트

## 결과

| 모델 | 반복 | 평균 총 응답 시간 | 평균 생성 속도 | 컨테이너 메모리 스냅샷 | Tool Calling | JSON Structured Output | 판정 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `qwen3.5:2b-q4_K_M` | 3 | 15.19초 | 4.20 tok/s | 2.33GiB | 성공 (`get_weather(city=서울)`) | 형식상 유효한 JSON 생성 | 1차 기준선 통과 |

| `qwen2.5:3b` | 3 | 29.68초 | 3.28 tok/s | 2.15GiB | 성공 (`get_weather(city=서울)`) | 형식상 유효한 JSON 생성 | 기능은 통과, 속도 열세 |
### `qwen3.5:2b-q4_K_M` 세부값

| 반복 | 총 응답 시간 | 출력 토큰 | 생성 속도 | 메모리 스냅샷 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 15.322초 | 62 | 4.17 tok/s | 2.313GiB |
| 2 | 15.091초 | 62 | 4.21 tok/s | 2.308GiB |
| 3 | 15.143초 | 62 | 4.22 tok/s | 2.374GiB |

## 해석

- 이 결과는 단일 요청·단일 모델 상주 조건의 측정값이다. FastAPI, Redis, PostgreSQL을 함께 띄운 최종 운영 메모리와 동시 요청 지연시간은 아직 측정하지 않았다.
- Tool Calling은 단일 도구 하나만 제공한 조건에서 확인했다. Structured Output은 JSON 파싱은 가능했으나, 추출된 key의 의미 적합성은 Application 검증 및 Phase 5 평가에서 별도로 검증해야 한다.
- 후보 모델을 비교한 뒤 최종 모델 태그 및 운영 설정을 `DECISIONS.md`에 확정한다.

## 선정

Phase 1 기본 모델은 `qwen3.5:2b-q4_K_M`로 선정한다. 3B 비교군도 기능은 통과했지만 생성 속도가 약 22% 낮았다. 2B도 한국어 응답, 단일 Tool Calling, JSON Structured Output을 모두 충족했으므로 4B 모델을 추가로 내려받을 근거가 없다.
