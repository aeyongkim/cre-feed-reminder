"""크레스티드 게코 급여 알리미."""

from datetime import date


def is_due(start_date: date, interval_days: int, today: date) -> bool:
    elapsed = (today - start_date).days
    return elapsed >= 0 and elapsed % interval_days == 0


def occurrence_index(start_date: date, interval_days: int, today: date) -> int:
    elapsed = (today - start_date).days
    return elapsed // interval_days
