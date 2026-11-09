#!/usr/bin/env bash
set -euo pipefail
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$project/../../.." && pwd)"
mode="${1:-corrected_x4}"
lighting="${2:-torch}"
case "$mode" in before|after|x4|full_x4|corrected_x4) ;; *) echo 'Use before, after, x4, full_x4 or corrected_x4' >&2; exit 2 ;; esac
case "$lighting" in normal) save=temple.oysav ;; torch) save=temple_torch.oysav ;;
    *) echo 'Use normal or torch' >&2; exit 2 ;; esac
stage="$repo/output/temple-textures-stage-20261008"
arguments=()
position=(-24644 -10305 -2200)
yaw=2.6
pitch=5.729578
if [[ "$mode" == x4 || "$mode" == full_x4 || "$mode" == corrected_x4 ]]; then
    arguments=(--settings "$project/references/demo_x4_settings.ini"
        --set video_quality.texture=x4 --set video_quality.textures=x4)
    position=(16400 -18592 752)
    yaw=0
    pitch=8.594367
fi
exec "$repo/tools/run_game.sh" --isolated "temple-textures-$mode-$lighting" --world mm6 \
    --save "$project/references/$save" --binary "$stage/openyamm" --assets "$stage/$mode/assets_dev" \
    "${arguments[@]}" --position "${position[@]}" --yaw-radians "$yaw" --pitch-degrees "$pitch" \
    --set video.resolution=1600x900 --seconds 0
