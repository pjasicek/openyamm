#!/usr/bin/env bash
# Prints the Android versionCode for a build: seconds from 2026-01-01 UTC to the commit's committer time.
# Every CI build uses it (.github/workflows/packages.yml), so any package of a newer commit updates any
# package of an older one, nightly or tagged; packages of the same commit share a code.
# The commit time comes from OPENYAMM_COMMIT_TIME (Unix seconds) when set, otherwise from HEAD.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
commit_time="${OPENYAMM_COMMIT_TIME:-$(git -C "$script_dir/.." log -1 --format=%ct HEAD)}"
scheme_epoch=1767225600 # 2026-01-01T00:00:00Z

if [[ ! "$commit_time" =~ ^[0-9]+$ ]]; then
    echo "Invalid commit time: $commit_time" >&2
    exit 1
fi

code=$(( commit_time - scheme_epoch ))

# The earlier run-number scheme (10000 + run * 100 + attempt) stayed below 1000000; Android caps codes at 2100000000
# (reached in 2092).
if (( code <= 1000000 || code > 2100000000 )); then
    echo "Commit time $commit_time gives Android versionCode $code outside 1000001..2100000000." >&2
    exit 1
fi

echo "$code"
