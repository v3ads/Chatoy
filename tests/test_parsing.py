from app.agents.parsing import (
    HANDOFF_MARKER,
    MarkdownStreamFilter,
    MarkerFilter,
    extract_first_json,
    parse_handoff,
    strip_inline_markdown,
)
from app.llm.base import ChainFilter


def _drain(filt, tokens: list[str]) -> str:
    return "".join(filt.feed(t) for t in tokens) + filt.flush()


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


def test_strip_inline_markdown_removes_tells_but_keeps_words():
    assert strip_inline_markdown("**Bold** and `code` here") == "Bold and code here"
    # Lone * / _ / # are left alone (hashtags, identifiers, prices).
    assert strip_inline_markdown("email_promo, #1, 5 * 3 stars") == "email_promo, #1, 5 * 3 stars"


def test_markdown_stream_filter_collapses_bold_split_across_tokens():
    # The two stars of ** arrive in separate tokens.
    assert _drain(MarkdownStreamFilter(), ["a*", "*b*", "*c"]) == "abc"
    assert _drain(MarkdownStreamFilter(), ["Make it ", "**bo", "ld**", " now"]) == "Make it bold now"
    # Single-star emphasis is preserved.
    assert _drain(MarkdownStreamFilter(), ["*keep*", " me"]) == "*keep* me"


def test_chain_filter_hides_marker_then_strips_markdown():
    out = _drain(
        ChainFilter(MarkerFilter(HANDOFF_MARKER), MarkdownStreamFilter()),
        ["Here ", "**you** go. ", HANDOFF_MARKER, ' {"asset_type": "ad"}'],
    )
    assert out == "Here you go. "
    assert "**" not in out and HANDOFF_MARKER not in out
