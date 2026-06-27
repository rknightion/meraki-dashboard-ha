"""apidrift CLI: derive the consumed surface, reduce specs, report drift.

Exit codes:
    0  no actionable drift (clean or INFO-only)
    2  usage / IO error
    3  actionable drift present (BREAKING or WARNING findings)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

from apidrift.reducer import index_operations, reduce_spec
from apidrift.report import Finding, has_actionable, render_json, render_markdown
from apidrift.scanner import consumed_operations
from apidrift.spec import load_spec, load_spec_bytes


def _load_live(args: argparse.Namespace) -> dict[str, Any]:
    if args.live_url:
        if not str(args.live_url).startswith("https://"):
            raise ValueError("--live-url must be https")
        with urllib.request.urlopen(args.live_url, timeout=60) as resp:  # noqa: S310
            return load_spec_bytes(resp.read())
    return load_spec(args.live)


def _emit(findings: list[Finding], fmt: str) -> None:
    print(render_json(findings) if fmt == "json" else render_markdown(findings))


def main(argv: list[str] | None = None) -> int:
    """Run the drift check and return the process exit code (0/2/3)."""
    ap = argparse.ArgumentParser(prog="apidrift")
    ap.add_argument(
        "--baseline", required=True, help="vendored baseline spec (.json/.json.gz)"
    )
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", help="path to a live spec file")
    source.add_argument("--live-url", help="https URL to fetch the live spec from")
    ap.add_argument(
        "--src",
        default="custom_components/meraki_dashboard",
        help="source tree to scan for consumed ops",
    )
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument(
        "--emit-reduced", help="dir to write reduced baseline.json + live.json"
    )
    args = ap.parse_args(argv)

    try:
        baseline = load_spec(args.baseline)
        live = _load_live(args)
    except Exception as exc:  # noqa: BLE001
        print(f"apidrift: load error: {exc}", file=sys.stderr)
        return 2

    consumed = consumed_operations(args.src)

    baseline_ops = set(index_operations(baseline))
    live_ops = set(index_operations(live))

    findings: list[Finding] = []
    # A consumed op is "missing" only if it was a real op in the baseline that is
    # now absent from the live spec — this filters scanner false positives.
    for op in sorted((consumed & baseline_ops) - live_ops):
        findings.append(
            Finding("BREAKING", "missing-op", op, "consumed op removed from live spec")
        )

    if args.emit_reduced:
        out = Path(args.emit_reduced)
        out.mkdir(parents=True, exist_ok=True)
        surface = consumed & (baseline_ops | live_ops)
        (out / "baseline.json").write_text(json.dumps(reduce_spec(baseline, surface)))
        (out / "live.json").write_text(json.dumps(reduce_spec(live, surface)))

    _emit(findings, args.format)
    return 3 if has_actionable(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
