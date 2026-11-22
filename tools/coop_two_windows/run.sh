#!/bin/bash
# Two real games on this PC: one hosts on Dagger Wound, the other joins it over UDP on localhost
# (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The replica as built"). Both run minimized and silent
# through tools/run_game.sh; each is driven by a menu-input tour (host_tour.yml, guest_tour.yml). The guest joins,
# stands in front of the host and walks from side to side. Screenshots of each game seeing the other, and both
# games' console lines, go to output/coop_two_windows/.
#   tools/coop_two_windows/run.sh
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$ROOT/output/coop_two_windows"
cd "$ROOT" || exit 1
mkdir -p "$OUT/captures"
sed "s|^output_dir: .*|output_dir: $OUT/captures|" "$HERE/host_tour.yml" > "$OUT/host_tour.yml"
sed "s|^output_dir: .*|output_dir: $OUT/captures|" "$HERE/guest_tour.yml" > "$OUT/guest_tour.yml"

SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_host --world mm8 --map out01.odm \
    --position 3560 7696 545 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds 80 \
    --set debug.menu_input_tour_path="$OUT/host_tour.yml" > "$OUT/host_run.log" 2>&1 &
HOST=$!
HOSTDIR=""

# The guest starts once the host listens.
for _ in $(seq 1 120); do
    HOSTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/host_run.log" 2>/dev/null | head -1)
    if [ -n "$HOSTDIR" ] && grep -qs "hosting on UDP" "$HOSTDIR/openyamm.log" "$HOSTDIR/measurement.log"; then
        break
    fi
    if ! kill -0 $HOST 2>/dev/null; then
        echo "the host ended before it listened; see $OUT/host_run.log"
        exit 1
    fi
    sleep 1
done

SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_guest --world mm8 --map out02.odm \
    --warmup 3 --seconds 60 \
    --set debug.menu_input_tour_path="$OUT/guest_tour.yml" > "$OUT/guest_run.log" 2>&1 &
GUEST=$!

while kill -0 $GUEST 2>/dev/null; do sleep 1; done
while kill -0 $HOST 2>/dev/null; do sleep 1; done

GUESTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/guest_run.log" | head -1)
grep -h -A24 "Menu tour console: > " "$HOSTDIR/measurement.log" | grep -v "^Menu tour: \|^--\|^\[" > "$OUT/host_console.txt"
grep -h -A8 "Menu tour console: > " "$GUESTDIR/measurement.log" | grep -v "^Menu tour: \|^--\|^\[" > "$OUT/guest_console.txt"
echo "captures: $OUT/captures"
echo "console lines: $OUT/host_console.txt $OUT/guest_console.txt"
grep -h "joined as player\|connection(s)" "$OUT/guest_console.txt" "$OUT/host_console.txt" | sort -u
