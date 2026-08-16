#!/usr/bin/env bash
# LOCAL AGENTS: If you are not a cloud agent, you must not execute this script.

set -euo pipefail

if [[ "${MERAKI_DASHBOARD_HA_CLOUD_SETUP:-}" != "1" ]]; then
    cat >&2 <<'EOF'
Refusing to run: this script provisions a disposable cloud agent sandbox with
system package installs, uv, and Backlog.md via sudo/root privileges. Local
agents and developer machines must not execute it.
If this is a cloud agent environment (Codex cloud tasks, Claude Code cloud
sessions), re-run with MERAKI_DASHBOARD_HA_CLOUD_SETUP=1 to confirm.
EOF
    exit 1
fi

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
    readonly UV_VERSION="0.11.26"
    case "$(uname -m)" in
        x86_64) UV_TARGET="x86_64-unknown-linux-gnu" ;;
        aarch64|arm64) UV_TARGET="aarch64-unknown-linux-gnu" ;;
        *)
            echo "Unsupported architecture for pinned uv install: $(uname -m)" >&2
            exit 1
            ;;
    esac
    readonly UV_ASSET="uv-${UV_TARGET}.tar.gz"
    readonly UV_BASE_URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}"
    UV_TMPDIR="$(mktemp -d)"
    trap 'rm -rf "${UV_TMPDIR}"' EXIT
    curl --proto '=https' --tlsv1.2 -LsSf -o "${UV_TMPDIR}/${UV_ASSET}" "${UV_BASE_URL}/${UV_ASSET}"
    curl --proto '=https' --tlsv1.2 -LsSf -o "${UV_TMPDIR}/${UV_ASSET}.sha256" "${UV_BASE_URL}/${UV_ASSET}.sha256"
    (cd "${UV_TMPDIR}" && sha256sum -c "${UV_ASSET}.sha256")
    tar -xzf "${UV_TMPDIR}/${UV_ASSET}" -C "${UV_TMPDIR}"
    install -Dm755 "${UV_TMPDIR}/${UV_TARGET}/uv" "${HOME}/.local/bin/uv"
    install -Dm755 "${UV_TMPDIR}/${UV_TARGET}/uvx" "${HOME}/.local/bin/uvx"
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
