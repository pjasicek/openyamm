# Sourced by the tests that build the calibration projects (native_vs_wasm.sh, sanitize.sh): the 22 L4 projects of
# the map studio's and the Xeen briefs. `calibration_projects <asset root> <Xeen root>` prints one line per project:
# "<name> <project folder> <asset root>"; the Xeen projects build against the Xeen root
# (output/studio_play/xeen_root), the others against the asset root.
calibration_projects()
{
    local assets="$1" xeen="$2" repo project name
    repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

    for project in "$repo"/devdocs/map_studio/briefs/*/L4; do
        name="$(basename "$(dirname "$project")")"
        echo "$name $project $assets"
    done

    for project in "$repo"/devdocs/xeen/briefs/*/L4; do
        name="$(basename "$(dirname "$project")")"
        echo "$name $project $xeen"
    done
}

# `build_fresh_copy <work folder> <project folder> <asset root> <oymap command...>`: copies the project to
# <work folder>/proj and builds it into <work folder>/out; the JSON report goes to stdout.json, the messages to
# stderr.txt, the exit code to rc.
build_fresh_copy()
{
    local work="$1" project="$2" assets="$3" rc=0
    shift 3
    mkdir -p "$work"
    cp -a "$project" "$work/proj"
    "$@" build "$work/proj" --assets "$assets" --out "$work/out" --json > "$work/stdout.json" 2> "$work/stderr.txt" \
        || rc=$?
    echo "$rc" > "$work/rc"
}
