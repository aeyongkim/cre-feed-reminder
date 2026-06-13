# 크레스티드 게코 급여 알리미 — 설계 문서

작성일: 2026-06-13

## 개요

설정 파일(YAML)에 개체별 급여 간격을 적어두면, GitHub Actions가 매일 한 번
실행되어 "오늘 급여할 개체"가 있을 때만 텔레그램으로 알림 메시지를 보낸다.

앱 UI나 서버 없이, 설정 파일 + 스케줄러 + 텔레그램 봇으로만 구성된 가벼운
독립 프로젝트다. 기존 `cre-app`(사육 종합 앱)과는 별개다.

## 목표 / 비목표

**목표**
- 개체별 급여 주기(N일 간격)에 맞춰 텔레그램으로 급여 알림을 받는다.
- 개체 관리는 설정 파일을 직접 편집하는 방식으로 한다.
- 서버 운영 없이 무료로 매일 자동 실행된다.

**비목표 (YAGNI)**
- 텔레그램 봇 명령어(/add, /done 등)로 개체를 관리하지 않는다.
- 급여 "완료" 추적·이력 기록을 하지 않는다 (순수 일정 기반 알림).
- 무게 기록, 산란 기록, 커뮤니티 등 사육 앱 기능은 포함하지 않는다.

## 아키텍처

```
geckos.yaml (개체 목록 + 급여 간격)
      │  읽기
      ▼
reminder.py  ──(오늘 급여 대상 계산)──▶ 텔레그램 봇 API ──▶ 내 텔레그램
      ▲
      │ 매일 1회 실행 (cron)
GitHub Actions workflow
```

구성요소 3개, 각각 역할이 명확하다.

- **`geckos.yaml`** — 사람이 직접 편집하는 데이터. 개체 이름/모프/급여간격/기준일.
- **`reminder.py`** — 순수 로직(오늘 누가 급여 대상인지 계산)과 발송을 함수로
  분리한다. 로직 함수는 외부 의존성 없이 테스트 가능해야 한다.
- **`.github/workflows/feed-reminder.yml`** — 매일 cron 실행. 텔레그램 봇 토큰과
  chat id는 GitHub Secrets로 보관한다.

## 데이터 모델 (`geckos.yaml`)

```yaml
geckos:
  - name: 아메
    morph: 릴리화이트       # 선택 항목
    interval_days: 3        # 3일마다 (기본값)
    start_date: 2026-06-13  # 이 날을 기준으로 간격 계산
  - name: 꿈이
    interval_days: 3
    start_date: 2026-06-13
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | O | 개체 이름 |
| `morph` | X | 모프(색상/유전자 표현형). 메시지에 괄호로 표시 |
| `interval_days` | O | 급여 간격(일). 기본 3 |
| `start_date` | O | 간격 계산 기준일 (YYYY-MM-DD) |

## 핵심 로직

**급여 대상 판정:** 어떤 개체가 오늘 급여 대상인지는 다음으로 판정한다.

```
elapsed = (today - start_date).days
due = elapsed >= 0 and elapsed % interval_days == 0
```

즉 `start_date`로부터 `interval_days`의 배수가 되는 날마다 급여일이다.
완료 추적은 하지 않으므로, 실제로 일찍/늦게 급여해도 알림 주기는 고정이다.

**메시지 포맷:** 오늘 급여 대상 개체를 모아 한 통으로 보낸다.

```
🦎 오늘 급여할 개체: 아메(릴리화이트), 꿈이
```

모프가 없는 개체는 이름만 표시한다. 대상이 한 마리도 없으면 **메시지를 보내지
않는다** (알림 피로 방지).

## 실행 / 스케줄

- **실행 환경:** GitHub Actions (무료, 상시 서버 불필요, 내 PC 꺼져 있어도 동작).
- **스케줄:** 매일 저녁 8시(KST) 1회. KST는 UTC+9이므로 cron은 UTC `0 11 * * *`.
- **수동 실행:** `workflow_dispatch`를 추가해 언제든 테스트 발송 가능.

## 보안

- 텔레그램 봇 토큰(`TELEGRAM_BOT_TOKEN`)과 채팅 ID(`TELEGRAM_CHAT_ID`)는
  GitHub Secrets에 저장하고, 워크플로에서 환경변수로 주입한다.
- 토큰·ID는 절대 저장소에 커밋하지 않는다.

## 기술 스택

- **언어:** Python 3
- **의존성:** `requests`(텔레그램 API 호출), `PyYAML`(설정 파일 파싱)
- **테스트:** pytest. 급여일 계산·메시지 포맷 등 순수 로직을 TDD로 검증.
  발송 함수는 mock으로 호출 여부만 확인.

## 테스트 전략

- `is_due(start_date, interval_days, today)` — 경계값(기준일 당일, 간격 배수일,
  비배수일, 기준일 이전) 검증.
- `geckos_due_today(config, today)` — 여러 개체 중 대상만 추려지는지 검증.
- `format_message(due_geckos)` — 모프 유무에 따른 표시, 빈 목록 처리 검증.
- 발송 흐름 — 대상이 없으면 텔레그램 API를 호출하지 않는지 mock으로 검증.

## 디렉터리 구조

```
cre-feed-reminder/
├── geckos.yaml
├── reminder.py
├── requirements.txt
├── tests/
│   └── test_reminder.py
├── .github/workflows/feed-reminder.yml
├── docs/superpowers/specs/2026-06-13-cre-feed-reminder-design.md
└── README.md   # 텔레그램 봇 생성 + Secrets 설정 안내
```
