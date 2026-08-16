---
id: MDH-0006
title: Add cloud environment setup script
status: Done
assignee:
  - '@codex'
created_date: '2026-08-16 11:36'
updated_date: '2026-08-16 11:39'
labels: []
dependencies: []
references:
  - 'https://learn.chatgpt.com/docs/environments/cloud-environment#manual-setup'
  - 'https://code.claude.com/docs/en/cloud-environments#setup-scripts'
modified_files:
  - scripts/cloud-environment-setup.sh
type: chore
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provision Codex cloud tasks and Claude Code cloud sessions with the repository development dependencies and Backlog.md CLI so agents can follow the project task workflow and run its required test and validation commands.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 scripts/cloud-environment-setup.sh begins with guidance that non-cloud local agents must not run it
- [x] #2 The script installs Backlog.md and verifies its CLI is available
- [x] #3 The script installs the project Python dependencies and tooling required by make lint, make test, and make validate
- [x] #4 The setup is idempotent and suitable for both Codex and Claude Code cloud setup-script execution
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 make lint
- [x] #2 make test
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a guarded, fail-fast Bash setup script that resolves the repository root and supports root or passwordless-sudo cloud images.
2. Install required Ubuntu system packages, uv, the pinned Backlog.md CLI, pre-commit, and frozen project dependencies with idempotent commands.
3. Validate shell syntax, tool availability, and the project lint/test gates; document and commit the result.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added the executable cloud-only setup script with Ubuntu packages, uv-managed locked dependencies, pre-commit, and pinned Backlog.md installation. Kept pre-commit outside pyproject.toml because it is environment bootstrap tooling and changing the lock with the locally available uv release introduced unrelated lockfile churn.

Validation passed: bash -n, executable/content assertions, git diff --check, make lint, and make test (687 passed, 82.84% coverage). The provisioning script itself was intentionally not executed by this non-cloud agent, as required by its local-agent guard comment.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added an executable Codex/Claude cloud setup script that installs Ubuntu build/runtime packages, uv and locked project dependencies, pre-commit, and Backlog.md 1.50.1. Verified syntax and required setup behavior statically, plus passed the full project lint and test gates (687 tests).
<!-- SECTION:FINAL_SUMMARY:END -->
