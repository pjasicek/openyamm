#!/bin/bash
# Texture pass: build into texpass/build_tour, install into texpass/mount_tour, copy the three map files into the
# scratch root (unlinking each first: nothing in root is written in place), then take the tour.
# Usage: tour.sh <tour.yml> <run name>
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd02/L4
X=$R/output/studio_cal/xd02
T=$X/texpass
cd $R
$O fmt $L >/dev/null
$O build $L --assets assets_dev --out $T/build_tour 2>&1 | grep -v "is named" | tail -2
$O install $L --build $T/build_tour --mount $T/mount_tour --assets assets_dev >/dev/null || exit 1
cp --remove-destination $T/mount_tour/worlds/mm7/maps/xeen_xd02.blv $X/root/worlds/mm7/maps/xeen_xd02.blv
cp --remove-destination $T/mount_tour/worlds/mm7/maps/xeen_xd02.scene.yml $X/root/worlds/mm7/maps/xeen_xd02.scene.yml
cp --remove-destination $T/mount_tour/worlds/mm7/events/maps/xeen_xd02.lua $X/root/worlds/mm7/events/maps/xeen_xd02.lua
cmp -s $T/mount_tour/engine/data_tables/map_stats.txt $X/root/engine/data_tables/map_stats.txt || echo "map_stats differs"
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "$2" --world mm7 --map xeen_xd02.blv --assets $X/root --warmup 3 --seconds 240 --set debug.screenshot_tour_path=$1
