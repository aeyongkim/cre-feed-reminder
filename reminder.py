"""크레스티드 게코 급여 알리미."""

from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests
import yaml


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_due(start_date: date, interval_days: int, today: date) -> bool:
    elapsed = (today - start_date).days
    return elapsed >= 0 and elapsed % interval_days == 0


def occurrence_index(start_date: date, interval_days: int, today: date) -> int:
    elapsed = (today - start_date).days
    return elapsed // interval_days


_SUPPLEMENTS = {
    "normal": "칼슘+비타민 섞기",
    "special": "MBD off 주기",
}


def supplement_note(category: str, idx: int) -> str | None:
    if idx % 2 != 0:
        return None
    return _SUPPLEMENTS.get(category)


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


def all_geckos_preview(config: dict) -> list:
    """급여일 여부와 무관하게 전체 개체를 첫 급여일(0회차)처럼 표시 — 테스트용."""
    result = []
    for g in config.get("geckos", []):
        result.append({
            "name": g["name"],
            "category": g["category"],
            "note": supplement_note(g["category"], 0),
        })
    return result


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
        blocks.append("\n".join(_section("✅ 정상 개체", normal)))
    if special:
        blocks.append("\n".join(_section("⚠️ 특별 관리 개체", special)))

    return "🦎 오늘 급여할 개체\n\n" + "\n\n".join(blocks)


CONFIG_PATH = "geckos.yaml"


def current_date() -> date:
    return datetime.now(ZoneInfo("Asia/Seoul")).date()


def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url, json={"chat_id": chat_id, "text": text}, timeout=10
    )
    if not resp.ok:
        raise RuntimeError(
            f"텔레그램 발송 실패 (HTTP {resp.status_code}): {resp.text}"
        )


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    config = load_config(CONFIG_PATH)

    force = os.environ.get("FORCE_SEND", "").strip().lower() in ("1", "true", "yes")
    if force:
        due = all_geckos_preview(config)
        prefix = "🧪 테스트 발송\n\n"
    else:
        due = geckos_due_today(config, current_date())
        prefix = ""

    message = format_message(due)
    if message is None:
        print("오늘 급여 대상 없음 — 메시지 미발송")
        return
    send_telegram(token, chat_id, prefix + message)
    print("급여 알림 발송 완료")


if __name__ == "__main__":
    main()
