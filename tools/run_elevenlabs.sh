#!/usr/bin/env bash
# Fixed entry point for reusable approval of budgeted ElevenLabs audio jobs (tools/audio/README.md).
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"
exec python3 "$repo_root/tools/audio/elevenlabs_gen.py" "$@"
