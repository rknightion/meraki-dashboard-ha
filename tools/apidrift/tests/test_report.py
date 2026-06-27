"""Tests for finding rendering."""

from __future__ import annotations

import json

from apidrift.report import Finding, has_actionable, render_json, render_markdown


def test_has_actionable() -> None:
    assert has_actionable([Finding("BREAKING", "k", "op", "d")])
    assert has_actionable([Finding("WARNING", "k", "op", "d")])
    assert not has_actionable([Finding("INFO", "k", "op", "d")])
    assert not has_actionable([])


def test_render_markdown_has_table_header() -> None:
    md = render_markdown([Finding("BREAKING", "missing-op", "getX", "detail")])
    assert "| Severity | Op | Kind | Detail |" in md
    assert "getX" in md


def test_render_markdown_empty_is_clean_message() -> None:
    assert "No drift" in render_markdown([])


def test_render_json_roundtrips() -> None:
    out = render_json(
        [
            Finding(
                "BREAKING",
                "missing-op",
                "getOrgs",
                "consumed op removed from live spec",
            )
        ]
    )
    parsed = json.loads(out)
    assert parsed[0]["kind"] == "missing-op"
    assert parsed[0]["severity"] == "BREAKING"
    assert parsed[0]["op"] == "getOrgs"
