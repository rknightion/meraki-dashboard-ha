#!/usr/bin/env bash
# LOCAL AGENTS: If you are not a cloud agent, you must not execute this script.

set -euo pipefail

readonly BACKLOG_VERSION="1.50.1"
readonly REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if ((EUID == 0)); then
    AS_ROOT=()
elif command -v sudo >/dev/null 2>&1; then
    AS_ROOT=(sudo)
else
    echo "This cloud image must provide root access or sudo." >&2
    exit 1
fi

echo "Installing system packages required by the development and validation tools..."
export DEBIAN_FRONTEND=noninteractive
"${AS_ROOT[@]}" apt-get update
"${AS_ROOT[@]}" apt-get install --yes --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    git \
    libpcap-dev \
    libturbojpeg0 \
    nodejs \
    npm \
    python3-dev

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
fi

echo "Installing Backlog.md ${BACKLOG_VERSION}..."
"${AS_ROOT[@]}" npm install --global "backlog.md@${BACKLOG_VERSION}"

echo "Installing the locked Python development environment and validation tools..."
cd "${REPOSITORY_ROOT}"
uv sync --frozen --all-groups
uv tool install --force pre-commit
export PATH="${HOME}/.local/bin:${PATH}"

echo "Verifying cloud task tools..."
uv run python --version
uv run ruff --version
uv run mypy --version
uv run pytest --version
pre-commit --version
backlog --version

echo "Cloud environment setup complete. Run 'make lint' and 'make test' to validate changes."
