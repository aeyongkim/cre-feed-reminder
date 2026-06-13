# 크레스티드 게코 급여 알리미 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 설정 파일(`geckos.yaml`)에 적힌 개체별 급여 주기를 읽어, 매일 GitHub Actions가 실행되어 "오늘 급여할 개체"가 있으면 텔레그램으로 알림을 보낸다.

**Architecture:** 순수 로직(급여일 계산·보충 회차·메시지 포맷)과 부수효과(설정 로드·텔레그램 발송)를 함수로 분리한 단일 모듈 `reminder.py`. 로직 함수는 외부 의존성 없이 테스트 가능하고, GitHub Actions cron이 매일 한 번 `main()`을 실행한다.

**Tech Stack:** Python 3, `PyYAML`(설정 파싱), `requests`(텔레그램 Bot API), `pytest`(테스트), GitHub Actions(cron 스케줄).

---

## File Structure

```
cre-feed-reminder/
├── reminder.py                       # 전체 로직 + 발송 + main()
├── geckos.yaml                       # 개체 목록 (사용자 편집)
├── requirements.txt                  # 의존성
├── tests/
│   └── test_reminder.py              # pytest 단위 테스트
├── .github/workflows/feed-reminder.yml  # 매일 cron 실행
├── README.md                         # 봇 생성 + Secrets + 편집 가이드 (한국어)
└── docs/superpowers/...              # 설계/계획 문서 (이미 존재)
```

**`reminder.py` 공개 함수 (인터페이스):**

| 함수 | 시그니처 | 책임 |
|------|----------|------|
| `load_config` | `(path: str) -> dict` | YAML 파일을 dict로 읽는다 |
| `is_due` | `(start_date: date, interval_days: int, today: date) -> bool` | 오늘이 급여일인가 |
| `occurrence_index` | `(start_date: date, interval_days: int, today: date) -> int` | 오늘이 몇 번째 급여일인가 (0-based) |
| `supplement_note` | `(category: str, idx: int) -> str \| None` | 이번 회차에 붙일 보충 문구 |
| `geckos_due_today` | `(config: dict, today: date) -> list[dict]` | 오늘 대상 개체 목록 `[{name, category, note}]` |
| `format_message` | `(due: list[dict]) -> str \| None` | 텔레그램 메시지 문자열 (대상 없으면 None) |
| `send_telegram` | `(token: str, chat_id: str, text: str) -> None` | Bot API로 발송 |
| `current_date` | `() -> date` | KST 기준 오늘 날짜 (테스트에서 monkeypatch 대상) |
| `main` | `() -> None` | 전체 흐름 오케스트레이션 |

---

## Task 1: 프로젝트 스캐폴딩

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_reminder.py` (빈 파일로 시작)
- Create: `reminder.py` (빈 파일로 시작)

- [ ] **Step 1: requirements.txt 작성**

Create `requirements.txt`:

```
PyYAML==6.0.2
requests==2.32.3
pytest==8.3.4
tzdata==2024.2
```

- [ ] **Step 2: 빈 소스/테스트 파일 생성**

Create `reminder.py`:

```python
"""크레스티드 게코 급여 알리미."""
```

Create `tests/test_reminder.py`:

```python
import reminder
```

- [ ] **Step 3: 의존성 설치 후 import 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pip install -r requirements.txt && python3 -m pytest -q`
Expected: pytest가 0개 테스트로 통과(또는 "no tests ran"). import 에러 없음.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt reminder.py tests/test_reminder.py
git commit -m "chore: scaffold project with deps and empty modules"
```

---

## Task 2: 급여일 계산 (`is_due`, `occurrence_index`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py`:

```python
from datetime import date
import reminder


def test_is_due_on_start_date():
    assert reminder.is_due(date(2026, 6, 14), 3, date(2026, 6, 14)) is True


def test_is_due_on_interval_multiple():
    assert reminder.is_due(date(2026, 6, 14), 3, date(2026, 6, 17)) is True


def test_is_not_due_on_non_multiple():
    assert reminder.is_due(date(2026, 6, 14), 3, date(2026, 6, 15)) is False


def test_is_not_due_before_start():
    assert reminder.is_due(date(2026, 6, 14), 3, date(2026, 6, 13)) is False


def test_occurrence_index_counts_feedings():
    assert reminder.occurrence_index(date(2026, 6, 14), 3, date(2026, 6, 14)) == 0
    assert reminder.occurrence_index(date(2026, 6, 14), 3, date(2026, 6, 17)) == 1
    assert reminder.occurrence_index(date(2026, 6, 14), 3, date(2026, 6, 20)) == 2
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: FAIL — `AttributeError: module 'reminder' has no attribute 'is_due'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py`:

```python
from datetime import date


def is_due(start_date: date, interval_days: int, today: date) -> bool:
    elapsed = (today - start_date).days
    return elapsed >= 0 and elapsed % interval_days == 0


def occurrence_index(start_date: date, interval_days: int, today: date) -> int:
    elapsed = (today - start_date).days
    return elapsed // interval_days
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add is_due and occurrence_index date logic"
```

---

## Task 3: 보충 문구 (`supplement_note`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

보충 문구는 회차가 짝수(0, 2, 4...)일 때 = 첫 급여일부터 격회로 붙는다.

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py`:

```python
def test_supplement_note_normal_on_even_occurrence():
    assert reminder.supplement_note("normal", 0) == "칼슘+비타민 섞기"
    assert reminder.supplement_note("normal", 2) == "칼슘+비타민 섞기"


def test_supplement_note_special_on_even_occurrence():
    assert reminder.supplement_note("special", 0) == "MBD off 주기"


def test_supplement_note_none_on_odd_occurrence():
    assert reminder.supplement_note("normal", 1) is None
    assert reminder.supplement_note("special", 1) is None
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: FAIL — `AttributeError: ... 'supplement_note'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py`:

```python
_SUPPLEMENTS = {
    "normal": "칼슘+비타민 섞기",
    "special": "MBD off 주기",
}


def supplement_note(category: str, idx: int) -> str | None:
    if idx % 2 != 0:
        return None
    return _SUPPLEMENTS.get(category)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add supplement_note (alternating from first feeding)"
```

---

## Task 4: 설정 로드 (`load_config`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py` (상단 import에 `import textwrap` 추가):

```python
def test_load_config_parses_yaml(tmp_path):
    cfg_file = tmp_path / "geckos.yaml"
    cfg_file.write_text(textwrap.dedent("""\
        geckos:
          - name: 아메
            category: normal
            interval_days: 3
            start_date: 2026-06-14
        """), encoding="utf-8")

    config = reminder.load_config(str(cfg_file))

    assert config["geckos"][0]["name"] == "아메"
    assert config["geckos"][0]["start_date"] == date(2026, 6, 14)
    assert config["geckos"][0]["interval_days"] == 3
```

(파일 맨 위 import 줄을 다음으로 확장:)

```python
from datetime import date
import textwrap
import reminder
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py::test_load_config_parses_yaml -q`
Expected: FAIL — `AttributeError: ... 'load_config'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py` (상단 import 보강):

```python
import yaml
```

```python
def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add load_config (YAML parsing)"
```

---

## Task 5: 오늘 대상 추리기 (`geckos_due_today`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

각 개체에 대해 `is_due`면 결과에 포함하고, `occurrence_index`로 보충 문구를 계산해 `{name, category, note}` dict로 담는다.

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py`:

```python
def _config():
    return {
        "geckos": [
            {"name": "아메", "category": "normal",
             "interval_days": 3, "start_date": date(2026, 6, 14)},
            {"name": "꿈이", "category": "normal",
             "interval_days": 3, "start_date": date(2026, 6, 14)},
            {"name": "별이", "category": "special",
             "interval_days": 3, "start_date": date(2026, 6, 14)},
        ]
    }


def test_geckos_due_today_includes_only_due_with_notes():
    # 첫 급여일(0회차): 셋 다 대상, 보충 문구 모두 표시
    due = reminder.geckos_due_today(_config(), date(2026, 6, 14))
    assert due == [
        {"name": "아메", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "꿈이", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "별이", "category": "special", "note": "MBD off 주기"},
    ]


def test_geckos_due_today_second_feeding_has_no_note():
    # 2번째 급여일(1회차): 대상이지만 보충 문구 없음
    due = reminder.geckos_due_today(_config(), date(2026, 6, 17))
    assert due[0] == {"name": "아메", "category": "normal", "note": None}


def test_geckos_due_today_empty_when_none_due():
    due = reminder.geckos_due_today(_config(), date(2026, 6, 15))
    assert due == []
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: FAIL — `AttributeError: ... 'geckos_due_today'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py`:

```python
def geckos_due_today(config: dict, today: date) -> list:
    result = []
    for g in config.get("geckos", []):
        start = g["start_date"]
        interval = g["interval_days"]
        if not is_due(start, interval, today):
            continue
        idx = occurrence_index(start, interval, today)
        result.append({
            "name": g["name"],
            "category": g["category"],
            "note": supplement_note(g["category"], idx),
        })
    return result
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add geckos_due_today selection"
```

---

## Task 6: 메시지 포맷 (`format_message`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

normal/special 두 섹션으로 나눠 출력. 대상 있는 섹션의 머리글만 표시. 보충 문구는 ` · 문구`로 붙임. 양쪽 다 비면 None.

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py`:

```python
def test_format_message_both_sections():
    due = [
        {"name": "아메", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "꿈이", "category": "normal", "note": None},
        {"name": "별이", "category": "special", "note": "MBD off 주기"},
    ]
    msg = reminder.format_message(due)
    assert msg == (
        "🦎 오늘 급여할 개체\n"
        "\n"
        "■ 정상 개체\n"
        "- 아메 · 칼슘+비타민 섞기\n"
        "- 꿈이\n"
        "\n"
        "■ 특별 관리 개체\n"
        "- 별이 · MBD off 주기"
    )


def test_format_message_only_normal_section():
    due = [{"name": "아메", "category": "normal", "note": None}]
    msg = reminder.format_message(due)
    assert msg == (
        "🦎 오늘 급여할 개체\n"
        "\n"
        "■ 정상 개체\n"
        "- 아메"
    )


def test_format_message_returns_none_when_empty():
    assert reminder.format_message([]) is None
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: FAIL — `AttributeError: ... 'format_message'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py`:

```python
def _section(title: str, geckos: list) -> list:
    lines = [title]
    for g in geckos:
        line = f"- {g['name']}"
        if g["note"]:
            line += f" · {g['note']}"
        lines.append(line)
    return lines


def format_message(due: list) -> str | None:
    if not due:
        return None
    normal = [g for g in due if g["category"] == "normal"]
    special = [g for g in due if g["category"] == "special"]

    blocks = []
    if normal:
        blocks.append("\n".join(_section("■ 정상 개체", normal)))
    if special:
        blocks.append("\n".join(_section("■ 특별 관리 개체", special)))

    return "🦎 오늘 급여할 개체\n\n" + "\n\n".join(blocks)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (15 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add format_message with normal/special sections"
```

---

## Task 7: 발송 + 오케스트레이션 (`send_telegram`, `current_date`, `main`)

**Files:**
- Modify: `reminder.py`
- Test: `tests/test_reminder.py`

`current_date()`는 KST 오늘을 돌려준다 (테스트에서 monkeypatch 가능하도록 분리). `main()`은 환경변수에서 토큰을 읽고, 대상이 있으면 발송, 없으면 발송하지 않는다.

- [ ] **Step 1: 실패하는 테스트 작성**

Add to `tests/test_reminder.py` (상단 import에 `from unittest import mock` 추가):

```python
def test_send_telegram_posts_to_bot_api():
    with mock.patch("reminder.requests.post") as post:
        post.return_value.raise_for_status.return_value = None
        reminder.send_telegram("TOKEN", "123", "안녕")
    post.assert_called_once_with(
        "https://api.telegram.org/botTOKEN/sendMessage",
        json={"chat_id": "123", "text": "안녕"},
        timeout=10,
    )


def test_main_sends_when_due(tmp_path, monkeypatch):
    cfg = tmp_path / "geckos.yaml"
    cfg.write_text(
        "geckos:\n"
        "  - name: 아메\n"
        "    category: normal\n"
        "    interval_days: 3\n"
        "    start_date: 2026-06-14\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "C")
    monkeypatch.setattr(reminder, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(reminder, "current_date", lambda: date(2026, 6, 14))
    sent = mock.Mock()
    monkeypatch.setattr(reminder, "send_telegram", sent)

    reminder.main()

    sent.assert_called_once()
    assert "아메" in sent.call_args.args[2]


def test_main_skips_when_none_due(tmp_path, monkeypatch):
    cfg = tmp_path / "geckos.yaml"
    cfg.write_text(
        "geckos:\n"
        "  - name: 아메\n"
        "    category: normal\n"
        "    interval_days: 3\n"
        "    start_date: 2026-06-14\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "C")
    monkeypatch.setattr(reminder, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(reminder, "current_date", lambda: date(2026, 6, 15))
    sent = mock.Mock()
    monkeypatch.setattr(reminder, "send_telegram", sent)

    reminder.main()

    sent.assert_not_called()
```

(파일 맨 위 import를 다음으로 확장:)

```python
from datetime import date
from unittest import mock
import textwrap
import reminder
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: FAIL — `AttributeError: ... 'requests'` / `'send_telegram'` / `'CONFIG_PATH'`

- [ ] **Step 3: 최소 구현**

Add to `reminder.py` (상단 import 보강):

```python
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
```

그리고 모듈 하단에:

```python
CONFIG_PATH = "geckos.yaml"


def current_date() -> date:
    return datetime.now(ZoneInfo("Asia/Seoul")).date()


def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url, json={"chat_id": chat_id, "text": text}, timeout=10
    )
    resp.raise_for_status()


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    config = load_config(CONFIG_PATH)
    due = geckos_due_today(config, current_date())
    message = format_message(due)
    if message is None:
        print("오늘 급여 대상 없음 — 메시지 미발송")
        return
    send_telegram(token, chat_id, message)
    print("급여 알림 발송 완료")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest tests/test_reminder.py -q`
Expected: PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add reminder.py tests/test_reminder.py
git commit -m "feat: add send_telegram and main orchestration"
```

---

## Task 8: 샘플 설정 파일 (`geckos.yaml`)

**Files:**
- Create: `geckos.yaml`

- [ ] **Step 1: 샘플 설정 작성**

Create `geckos.yaml`:

```yaml
# 크레스티드 게코 급여 알리미 설정
# 개체를 추가/삭제하려면 아래 목록을 편집하세요.
#   name:          개체 이름
#   category:      normal(정상) 또는 special(특별 관리)
#   interval_days: 급여 간격(일). 보통 3
#   start_date:    급여 시작 기준일 (YYYY-MM-DD)
geckos:
  - name: 예시개체-정상
    category: normal
    interval_days: 3
    start_date: 2026-06-14

  - name: 예시개체-특별관리
    category: special
    interval_days: 3
    start_date: 2026-06-14
```

- [ ] **Step 2: 로컬에서 로직 동작 확인 (발송 없이)**

Run:
```bash
cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -c "
import reminder
from datetime import date
cfg = reminder.load_config('geckos.yaml')
due = reminder.geckos_due_today(cfg, date(2026, 6, 14))
print(reminder.format_message(due))
"
```
Expected: 두 섹션이 포함된 메시지 문자열이 출력됨 (정상/특별관리 각각 보충 문구 포함).

- [ ] **Step 3: Commit**

```bash
git add geckos.yaml
git commit -m "feat: add sample geckos.yaml config"
```

---

## Task 9: GitHub Actions 워크플로

**Files:**
- Create: `.github/workflows/feed-reminder.yml`

매일 저녁 8시 KST(= UTC 11:00)에 실행. 수동 실행(`workflow_dispatch`)도 가능.

- [ ] **Step 1: 워크플로 작성**

Create `.github/workflows/feed-reminder.yml`:

```yaml
name: feed-reminder

on:
  schedule:
    # 매일 저녁 8시 KST = 11:00 UTC
    - cron: "0 11 * * *"
  workflow_dispatch: {}

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Send feeding reminder
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python reminder.py
```

- [ ] **Step 2: YAML 유효성 확인**

Run:
```bash
cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/feed-reminder.yml')); print('valid')"
```
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/feed-reminder.yml
git commit -m "ci: add daily GitHub Actions schedule (20:00 KST)"
```

---

## Task 10: README (한국어 사용 가이드)

**Files:**
- Create: `README.md`

- [ ] **Step 1: README 작성**

Create `README.md`:

````markdown
# 크레스티드 게코 급여 알리미

설정 파일에 적은 개체별 급여 주기에 맞춰, 매일 저녁 8시(KST)에
"오늘 급여할 개체"를 텔레그램으로 알려줍니다. 대상이 없는 날은 보내지 않습니다.

## 처음 설정 (1회)

### 1. 텔레그램 봇 만들기
1. 텔레그램에서 `@BotFather` 검색 → `/newbot` → 안내대로 이름 입력
2. 받은 **봇 토큰**(`123456:ABC...`)을 복사해 둡니다.

### 2. 내 chat id 알아내기
1. 방금 만든 봇과 대화를 시작(아무 메시지나 전송)
2. 브라우저에서 `https://api.telegram.org/bot<봇토큰>/getUpdates` 접속
3. 응답에서 `"chat":{"id": 숫자}` 의 **숫자**가 chat id 입니다.

### 3. GitHub Secrets 등록
저장소 → Settings → Secrets and variables → Actions → **New repository secret**
- `TELEGRAM_BOT_TOKEN` : 봇 토큰
- `TELEGRAM_CHAT_ID` : chat id

## 개체 추가/수정/삭제

`geckos.yaml` 파일만 편집하면 됩니다. GitHub 웹에서 ✏️로 바로 고치고
"Commit changes" 하면 다음 알림부터 반영됩니다.

```yaml
geckos:
  - name: 아메            # 개체 이름
    category: normal      # normal(정상) / special(특별 관리)
    interval_days: 3      # 며칠마다 급여
    start_date: 2026-06-14  # 급여 시작 기준일
```

- **이름 변경:** `name` 값 수정
- **개체 추가:** 블록 하나를 복사해 붙이고 값 수정
- **개체 삭제:** 해당 블록 전체 삭제

## 보충 안내 규칙

각 개체의 급여 회차가 **첫 급여일부터 격회(1·3·5번째)** 일 때 문구가 함께 표시됩니다.
- `normal` → `칼슘+비타민 섞기`
- `special` → `MBD off 주기`

## 수동 테스트

저장소 → Actions → **feed-reminder** → **Run workflow** 로 즉시 발송 테스트가 가능합니다.

## 로컬 개발

```bash
pip install -r requirements.txt
pytest -q
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add Korean setup and usage guide"
```

---

## Task 11: 최종 검증

**Files:** 없음 (검증만)

- [ ] **Step 1: 전체 테스트 통과 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && python3 -m pytest -q`
Expected: PASS (18 tests), 실패·에러 없음.

- [ ] **Step 2: main 흐름 스모크 테스트 (발송 없이 미발송 경로)**

Run:
```bash
cd /Users/ny0kimm/projects/cre-feed-reminder && TELEGRAM_BOT_TOKEN=x TELEGRAM_CHAT_ID=y python3 -c "
import reminder
from datetime import date
reminder.current_date = lambda: date(2026, 6, 15)  # 대상 없는 날
reminder.main()
"
```
Expected: `오늘 급여 대상 없음 — 메시지 미발송` 출력, 네트워크 호출 없음.

- [ ] **Step 3: 작업 트리 깨끗한지 확인**

Run: `cd /Users/ny0kimm/projects/cre-feed-reminder && git status --short`
Expected: 출력 없음 (모두 커밋됨).

---

## Self-Review 결과

- **Spec 커버리지:** 데이터 모델(Task 4,8) · 급여일 판정(Task 2) · 보충 회차(Task 3) · 대상 추출(Task 5) · 두 섹션 메시지(Task 6) · 미발송 정책(Task 6,7) · KST 저녁 8시 cron(Task 9) · Secrets 보안(Task 9,10) · 테스트 전략(Task 2~7) — 모두 대응 태스크 있음.
- **Placeholder:** 없음. 모든 코드/명령 구체화됨.
- **타입 일관성:** `geckos_due_today` 반환 dict 키(`name`/`category`/`note`)가 Task 5·6·7에서 일치. `CONFIG_PATH`·`current_date`·`send_telegram` 이름이 Task 7과 테스트에서 일치.
