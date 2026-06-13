from datetime import date
import textwrap
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
