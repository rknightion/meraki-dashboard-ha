"""Tests for backlog-guard.py.

Run with: python3 .claude/hooks/backlog-guard_test.py

The denied flags are built by concatenation (`"--" + "notes"`) so that this file's
own contents, and the command line used to run it, never contain the literal flag
the hook denies — otherwise the hook blocks its own test harness.

Both directions are asserted: unsafe forms must exit 2, and safe forms must exit 0.
A guard that only ever says no is indistinguishable from a broken one.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, ".claude", "hooks", "backlog-guard.py")
env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)

N = "--" + "notes"
P = "--" + "plan"

cases = [
    # --- must BLOCK (exit 2) ---
    ("bare notes flag",       {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit mdh-0001 {N} hi"}}, 2),
    ("bare plan flag",        {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit mdh-0001 {P} hi"}}, 2),
    ("equals form",           {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit mdh-0001 {N}=hi"}}, 2),
    ("flag at end of line",   {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit mdh-0001 {N}"}}, 2),
    ("edit task md",          {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/tasks/mdh-0001 - x.md"}}, 2),
    ("write doc md",          {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/backlog/docs/doc-0002 - y.md"}}, 2),
    ("edit completed md",     {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/completed/mdh-0009 - z.md"}}, 2),
    ("edit decisions md",     {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/decisions/decision-1 - d.md"}}, 2),

    # --- must ALLOW (exit 0) ---
    ("append-notes allowed",  {"tool_name": "Bash", "tool_input": {"command": "backlog task edit mdh-0001 --append-notes hi"}}, 0),
    ("append-plan allowed",   {"tool_name": "Bash", "tool_input": {"command": "backlog task edit mdh-0001 --append-plan hi"}}, 0),
    ("finalize in one call",  {"tool_name": "Bash", "tool_input": {"command": "backlog task edit mdh-0001 --check-ac 1 -s Done"}}, 0),
    ("task list allowed",     {"tool_name": "Bash", "tool_input": {"command": "backlog task list --plain"}}, 0),
    ("doc update allowed",    {"tool_name": "Bash", "tool_input": {"command": "backlog doc update doc-0002 --content x"}}, 0),
    ("non-backlog cmd",       {"tool_name": "Bash", "tool_input": {"command": f"mytool {N} foo"}}, 0),
    ("make test allowed",     {"tool_name": "Bash", "tool_input": {"command": "make lint && make test"}}, 0),
    ("config.yml allowed",    {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/config.yml"}}, 0),
    ("source file allowed",   {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/custom_components/meraki_dashboard/sensor.py"}}, 0),
    ("test file allowed",     {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/tests/test_sensor.py"}}, 0),
    ("AGENTS.md allowed",     {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/AGENTS.md"}}, 0),
    ("archive json allowed",  {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/archive/github-issues-2026-08-14.json"}}, 0),
]

fails = 0
for name, payload, want in cases:
    r = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                       capture_output=True, text=True, env=env)
    ok = r.returncode == want
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  exit={r.returncode} want={want}  {name}")

# garbage stdin must never block
r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, env=env)
ok = r.returncode == 0
fails += not ok
print(f"{'PASS' if ok else 'FAIL'}  exit={r.returncode} want=0  garbage stdin never blocks")

total = len(cases) + 1
print(f"\n{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
