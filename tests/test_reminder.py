from datetime import date
from unittest import mock
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


def test_supplement_note_even_occurrence_is_calcium_for_both():
    assert reminder.supplement_note("normal", 0) == "칼슘+비타민 섞기"
    assert reminder.supplement_note("normal", 2) == "칼슘+비타민 섞기"
    assert reminder.supplement_note("special", 0) == "칼슘+비타민 섞기"


def test_supplement_note_odd_occurrence_differs_by_category():
    assert reminder.supplement_note("normal", 1) == "슈퍼푸드만"
    assert reminder.supplement_note("special", 1) == "MBD off 주기"


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
    # 첫 급여일(0회차): 셋 다 대상, 모두 칼슘+비타민
    due = reminder.geckos_due_today(_config(), date(2026, 6, 14))
    assert due == [
        {"name": "아메", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "꿈이", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "별이", "category": "special", "note": "칼슘+비타민 섞기"},
    ]


def test_geckos_due_today_second_feeding_alternate_notes():
    # 2번째 급여일(1회차): 정상은 슈퍼푸드만, 특별은 MBD off
    due = reminder.geckos_due_today(_config(), date(2026, 6, 17))
    assert due[0] == {"name": "아메", "category": "normal", "note": "슈퍼푸드만"}
    assert due[2] == {"name": "별이", "category": "special", "note": "MBD off 주기"}


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
        "✅ 정상 개체\n"
        "- 아메 · 칼슘+비타민 섞기\n"
        "- 꿈이\n"
        "\n"
        "⚠️ 특별 관리 개체\n"
        "- 별이 · MBD off 주기"
    )


def test_format_message_only_normal_section():
    due = [{"name": "아메", "category": "normal", "note": None}]
    msg = reminder.format_message(due)
    assert msg == (
        "🦎 오늘 급여할 개체\n"
        "\n"
        "✅ 정상 개체\n"
        "- 아메"
    )


def test_format_message_returns_none_when_empty():
    assert reminder.format_message([]) is None


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


def test_all_geckos_preview_marks_all_with_first_feeding_note():
    preview = reminder.all_geckos_preview(_config())
    assert preview == [
        {"name": "아메", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "꿈이", "category": "normal", "note": "칼슘+비타민 섞기"},
        {"name": "별이", "category": "special", "note": "칼슘+비타민 섞기"},
    ]


def test_main_force_send_sends_even_when_not_due(tmp_path, monkeypatch):
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
    monkeypatch.setenv("FORCE_SEND", "true")
    monkeypatch.setattr(reminder, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(reminder, "current_date", lambda: date(2026, 6, 15))  # 급여일 아님
    sent = mock.Mock()
    monkeypatch.setattr(reminder, "send_telegram", sent)

    reminder.main()

    sent.assert_called_once()
    assert "아메" in sent.call_args.args[2]
    assert "테스트" in sent.call_args.args[2]


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
