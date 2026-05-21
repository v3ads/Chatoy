from app.agents.parsing import (
    HANDOFF_MARKER,
    MarkerFilter,
    extract_first_json,
    parse_handoff,
)


def test_extract_first_json_handles_nested_and_trailing_prose():
    text = 'noise {"a": 1, "b": {"c": [2, 3]}} trailing text'
    assert extract_first_json(text) == {"a": 1, "b": {"c": [2, 3]}}


def test_extract_first_json_tolerates_braces_in_strings():
    text = '{"k": "a } b { c"}'
    assert extract_first_json(text) == {"k": "a } b { c"}


def test_extract_first_json_returns_none_when_absent():
    assert extract_first_json("no json here") is None


def test_parse_handoff_strips_marker_and_returns_strategy():
    text = (
        "Great, I have what I need.\n"
        f'{HANDOFF_MARKER} {{"asset_type": "email_promo", "marketing_angle": "x"}}'
    )
    strategy, visible = parse_handoff(text)
    assert strategy == {"asset_type": "email_promo", "marketing_angle": "x"}
    assert visible == "Great, I have what I need."
    assert HANDOFF_MARKER not in visible


def test_parse_handoff_without_marker_is_diagnose():
    strategy, visible = parse_handoff("What is your audience?")
    assert strategy is None
    assert visible == "What is your audience?"


def test_marker_filter_suppresses_from_marker_onward_split_across_tokens():
    f = MarkerFilter(HANDOFF_MARKER)
    out = []
    # Feed the marker split across multiple tokens.
    for tok in ["Hello ", "there.", " PROMPT_", "HANDOFF:", ' {"a":1}']:
        out.append(f.feed(tok))
    out.append(f.flush())
    visible = "".join(out)
    assert "Hello there." in visible
    assert HANDOFF_MARKER not in visible
    assert "{" not in visible
