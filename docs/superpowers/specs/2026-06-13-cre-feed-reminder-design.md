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
- 개체를 정상/특별 관리로 나눠 메시지를 두 섹션으로 구분한다.
- 두 번에 한 번 급여 시 보충 안내(칼슘+비타민 섞기 / MBD off 주기)를 함께 표시한다.
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
    category: normal        # normal | special
    interval_days: 3        # 3일마다 (기본값)
    start_date: 2026-06-14  # 이 날을 기준으로 간격 계산 (= 내일)
  - name: 별이
    category: special
    interval_days: 3
    start_date: 2026-06-14
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | O | 개체 이름 |
| `category` | O | `normal`(정상) 또는 `special`(특별 관리) |
| `interval_days` | O | 급여 간격(일). 기본 3 |
| `start_date` | O | 간격 계산 기준일 (YYYY-MM-DD). 기본값은 내일 |

## 핵심 로직

**급여 대상 판정:** 어떤 개체가 오늘 급여 대상인지는 다음으로 판정한다.

```
elapsed = (today - start_date).days
due = elapsed >= 0 and elapsed % interval_days == 0
```

즉 `start_date`로부터 `interval_days`의 배수가 되는 날마다 급여일이다.
완료 추적은 하지 않으므로, 실제로 일찍/늦게 급여해도 알림 주기는 고정이다.

**급여 회차 계산:** 오늘이 그 개체의 몇 번째 급여일인지(0-based)는 다음과 같다.

```
occurrence_index = elapsed // interval_days   # 0, 1, 2, ...
```

**보충제 표시 (두 번에 한 번):** 각 개체는 자기 급여 회차가 "두 번에 한 번"
돌아올 때 보충 안내 문구를 함께 표시한다. 기준은 `occurrence_index % 2 == 1`,
즉 **2번째·4번째·6번째 급여일**에 표시한다 (첫 급여일은 표시 없음).

- `category: normal` → `칼슘+비타민 섞기`
- `category: special` → `MBD off 주기`

> 가정: 보충 문구는 첫 급여(0회차)에는 없고 2회차부터 격회로 붙는다.
> 첫 급여부터 붙기를 원하면 판정을 `% 2 == 0`으로 바꾸면 된다.

**메시지 포맷:** 오늘 급여 대상 개체를 `normal` / `special` 두 섹션으로 나눠
한 통으로 보낸다. 보충 문구는 해당 개체 옆에 붙인다.

```
🦎 오늘 급여할 개체

■ 정상 개체
- 아메 · 칼슘+비타민 섞기
- 꿈이

■ 특별 관리 개체
- 별이 · MBD off 주기
```

규칙:
- 보충 회차가 아닌 개체는 ` · 문구` 없이 이름만 표시한다.
- 한 섹션에 대상이 없으면 그 섹션 머리글은 생략한다.
- 양쪽 모두 대상이 한 마리도 없으면 **메시지를 보내지 않는다** (알림 피로 방지).

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
- `occurrence_index(start_date, interval_days, today)` — 0회차/1회차/2회차 계산.
- `supplement_note(category, occurrence_index)` — normal/special별 문구, 격회
  표시(0회차 없음, 1회차 있음) 검증.
- `geckos_due_today(config, today)` — 여러 개체 중 대상만 추려지는지 검증.
- `format_message(due_geckos)` — normal/special 섹션 분리, 보충 문구 유무, 한
  섹션만 있는 경우, 빈 목록 처리 검증.
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
