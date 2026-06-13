"""크레스티드 게코 급여 알리미."""

from __future__ import annotations

from datetime import date

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
