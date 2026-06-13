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


def test_supplement_note_normal_on_even_occurrence():
    assert reminder.supplement_note("normal", 0) == "칼슘+비타민 섞기"
    assert reminder.supplement_note("normal", 2) == "칼슘+비타민 섞기"


def test_supplement_note_special_on_even_occurrence():
    assert reminder.supplement_note("special", 0) == "MBD off 주기"


def test_supplement_note_none_on_odd_occurrence():
    assert reminder.supplement_note("normal", 1) is None
    assert reminder.supplement_note("special", 1) is None
