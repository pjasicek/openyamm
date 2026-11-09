#!/usr/bin/env bash
# Build several ids, at most $JOBS at a time (default 3); logs in work/<id>.build.log. Usage: build_many.sh <id>... [-- --install]
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ids=(); extra=()
while [[ $# -gt 0 ]]; do if [[ "$1" == "--" ]]; then shift; extra=("$@"); break; fi; ids+=("$1"); shift; done
printf '%s\n' "${ids[@]}" | xargs -P "${JOBS:-3}" -I{} bash -c "'$here/build.sh' {} ${extra[*]} > '$here/work/{}.build.log' 2>&1; echo DONE {} \$?"
