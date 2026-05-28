#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

python_bin="${PYTHON:-python3}"
extracted_root="${MM9_EXTRACTED_ROOT:-mm9/extracted}"
world_roots=(
    "assets_dev/worlds/mm9"
    "assets_editor_dev/worlds/mm9"
)
dry_run=0

while [[ $# -gt 0 ]]
do
    case "$1" in
        --extracted-root)
            extracted_root="$2"
            shift 2
            ;;
        --world-root)
            world_roots=("$2")
            shift 2
            ;;
        --add-world-root)
            world_roots+=("$2")
            shift 2
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            cat <<'EOF'
usage: regenerate_mm9_static_assets.sh [options]

Copies MM9 static assets that remain in source formats into OpenYAMM MM9 world roots.

Options:
  --extracted-root PATH   Extracted MM9 REZ root. Default: mm9/extracted
  --world-root PATH       Replace destination roots with PATH.
  --add-world-root PATH   Add another destination root.
  --dry-run               Print copy actions without writing files.
EOF
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

args=(--extracted-root "${extracted_root}")
for world_root in "${world_roots[@]}"
do
    args+=(--world-root "${world_root}")
done
if [[ "${dry_run}" == 1 ]]
then
    args+=(--dry-run)
fi

"${python_bin}" tools/mm9_import_discovery/sync_static_assets.py "${args[@]}"
