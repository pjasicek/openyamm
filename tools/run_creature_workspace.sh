#!/usr/bin/env bash
# Stable entry point for sandboxed workspace writes; ownership and locking stay in the helper.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"
exec python3 "$repo_root/tools/creature_workspace.py" "$@"
