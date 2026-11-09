#!/bin/sh
set -eu

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
play_dir="$project_dir/local_playtest"
if [ "${1-}" = "--restage" ]; then
    shift
    python3 "$project_dir/stage_playtest.py"
elif [ ! -d "$play_dir" ]; then
    python3 "$project_dir/stage_playtest.py"
fi

exec "$play_dir/play-mm5.sh" "$@"
