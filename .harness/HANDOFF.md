# HANDOFF — 세션별 인수인계 로그

> append-only. 새 항목을 **맨 아래에** 추가한다.
> 여기에는 "이번 세션에 무엇을 했고 다음 세션이 무엇부터 하면 되는지"만 적는다.
> Phase 완료 요약은 `STATE.md`, 결정 이유는 `DECISIONS.md`가 소유한다.

---

## 2026-09-10 — 세션 1 (Claude Code)

**브랜치:** `phase0/environment-probe`

### 한 일

1. **Phase 0 환경 조사.** 개발 머신(Windows 데스크톱) 사양·툴체인을 실측했다. `strands-agents` 1.54.0의 Ollama 연동 사양과 Ollama 라이브러리의 현재 Qwen 라인업을 공식 소스로 확인했다. 결과는 `ARCHITECTURE.md`와 `PLAN.md`에 있다.
2. **`scripts/phase0_probe.sh` 작성.** 미니PC 사양 측정용. 읽기 전용이고 coreutils 외 의존성이 없다. AVX/AVX2 지원 여부를 함께 검사한다 — CPU 추론 처리량을 크게 가르는 요소다.
3. **`.gitattributes` 추가.** `*.sh`를 LF로 고정. Windows에서 커밋해 Linux에서 실행하므로 CRLF가 섞이면 셔뱅이 깨진다.
4. **`CLAUDE.md` / `AGENTS.md` 재작성.** 이전 Java(Gradle/JPA/MSA) 프로젝트용 지침을 이 Python 프로젝트에 맞게 전면 개편했다. `scripts/check_docs_sync.sh`로 두 파일의 바이트 동일성을 검증한다.
5. **`.harness/` 문서 체계 신설.** 7개 문서를 지금까지의 조사 결과로 채웠다.

### 다음 세션이 할 일

**Phase 0은 아직 끝나지 않았다.** 다음 한 가지에 막혀 있다.

> **미니PC에서 `scripts/phase0_probe.sh`를 실행한 출력이 필요하다.**

사용자가 미니PC를 가지고 있다고 확인했고 사양을 알려주기로 했으나, 아직 받지 못했다. 출력을 받으면:

1. `ARCHITECTURE.md` 4.2절(현재 "미실측")을 실제 값으로 채운다.
2. MemAvailable과 AVX2 지원 여부로 `PLAN.md`의 모델 후보 A~E 중 실행 가능한 것을 좁힌다.
3. Phase 0-B(Ollama 설치 + 모델 벤치마크)로 진행한다.

### 주의할 것

- **개발 머신에서 모델 벤치마크를 돌리지 말 것.** 여기엔 GPU가 있고 미니PC엔 없을 가능성이 높아 결과가 이전되지 않는다. 사용자가 이 점을 명시적으로 지적했고, 그래서 이 머신에 Ollama를 설치하지 않았다. 근거는 `DECISIONS.md` 참조.
- **아직 애플리케이션 코드가 하나도 없다.** `pyproject.toml`도 `app/`도 `tests/`도 없다. 있다고 가정하고 참조하지 말 것.
- **thinking 모드 끄는 경로와 `num_ctx` 적용 여부는 미검증이다.** Strands 문서에서 확인하지 못했다. Phase 1에서 실제로 돌려보고 확인할 것. 추측으로 구현하지 말 것.
- `CLAUDE.md`를 고치면 반드시 `cp CLAUDE.md AGENTS.md` 후 `sh scripts/check_docs_sync.sh`로 검증할 것.
