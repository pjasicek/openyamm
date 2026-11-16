#!/usr/bin/env bash
# Runs `oymap audit` over every map of an asset root and prints, per world, how many maps loaded and how many
# findings of each kind there are. A map that fails to load is listed. Usage: tests/audit_all.sh [asset root]
set -uo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:-$studio/../assets_dev}"
work="$(mktemp -d)"

for world in $(ls "$root/worlds"); do
    [ -d "$root/worlds/$world/maps" ] || continue
    total=0
    loaded=0
    : > "$work/findings"
    for map in $(cd "$root/worlds/$world/maps" && ls | grep -E '\.(odm|blv)$'); do
        total=$((total + 1))
        if "$studio/build/oymap" audit "$map" --world "$world" --assets "$root" --json > "$work/one.json" 2> "$work/err"; then
            :
        fi
        if [ -s "$work/one.json" ]; then
            loaded=$((loaded + 1))
            python3 - "$work/one.json" "$map" >> "$work/findings" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
for warning in doc["warnings"]:
    print("load.warning", sys.argv[2], warning[:90])
for finding in doc["findings"]:
    print(finding["severity"] + ":" + finding["code"])
PY
        else
            echo "NOT LOADED $world/$map: $(head -c 200 "$work/err")"
        fi
    done
    echo "$world: loaded $loaded of $total maps"
    grep -v '^load.warning' "$work/findings" | sort | uniq -c | sed 's/^/    /'
    grep '^load.warning' "$work/findings" | cut -d' ' -f3- | sed 's/ [0-9a-z_]*\.lua)/ <map>.lua)/' | sort | uniq -c | sed 's/^/    warning /' | head -6
done
