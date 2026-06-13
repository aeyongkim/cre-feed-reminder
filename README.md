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
