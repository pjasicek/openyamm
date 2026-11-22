#!/bin/bash
# Three programs on this PC: the lobby service, a game that hosts through it and a game that joins by the session's
# code (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The lobby as built"). The joining game first lists
# what it can find (the host on the local network and the lobby's session), then joins by the code.
#   tools/coop_two_windows/run_lobby.sh [relay]
# With `relay` the joining game takes the lobby's relay and no direct path.
# Output: output/coop_lobby/ (both games' console lines, the lobby's log).
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$ROOT/output/coop_lobby"
MODE="${1:-code}"
LOBBY_PORT=27910
cd "$ROOT" || exit 1
mkdir -p "$OUT"

./build/tools/openyamm_lobby_server --port $LOBBY_PORT --relay-ports 4 > "$OUT/lobby.log" 2>&1 &
LOBBY=$!
sleep 1
if ! kill -0 $LOBBY 2>/dev/null; then
    echo "the lobby service did not start; see $OUT/lobby.log"
    exit 1
fi

cat > "$OUT/host_tour.yml" <<TOUR
output_dir: $OUT
exit: true
steps:
  - wait: 1
  - console: coop host lobby 127.0.0.1:$LOBBY_PORT The test world
  - wait: 3
  - console: coop net
  - wait: 30
  - console: coop net
  - console: coop show
  - wait: 4
TOUR

SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_lobby_host --world mm8 --map out01.odm \
    --position 3560 7696 545 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds 70 \
    --set debug.menu_input_tour_path="$OUT/host_tour.yml" > "$OUT/host_run.log" 2>&1 &
HOST=$!
CODE=""

# The joining game starts once the lobby has given the host its code.
for _ in $(seq 1 120); do
    HOSTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/host_run.log" 2>/dev/null | head -1)
    if [ -n "$HOSTDIR" ]; then
        CODE=$(grep -hs -o "lobby code [A-Z0-9]*" "$HOSTDIR/openyamm.log" "$HOSTDIR/measurement.log" | head -1 | sed 's/lobby code //')
    fi
    [ -n "$CODE" ] && break
    if ! kill -0 $HOST 2>/dev/null; then
        echo "the host ended before the lobby answered; see $OUT/host_run.log and $OUT/lobby.log"
        kill $LOBBY 2>/dev/null
        exit 1
    fi
    sleep 1
done

JOIN="coop join code $CODE 127.0.0.1:$LOBBY_PORT"
[ "$MODE" = "relay" ] && JOIN="coop join relay $CODE 127.0.0.1:$LOBBY_PORT"

cat > "$OUT/guest_tour.yml" <<TOUR
output_dir: $OUT
exit: true
steps:
  - wait: 1
  - console: coop find 127.0.0.1:$LOBBY_PORT
  - console: $JOIN
  - wait: 8
  - console: coop net
  - wait: 6
  - console: coop net
  - wait: 2
TOUR

SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_lobby_guest --world mm8 --map out02.odm \
    --warmup 3 --seconds 40 \
    --set debug.menu_input_tour_path="$OUT/guest_tour.yml" > "$OUT/guest_run.log" 2>&1 &
GUEST=$!

while kill -0 $GUEST 2>/dev/null; do sleep 1; done
while kill -0 $HOST 2>/dev/null; do sleep 1; done
kill $LOBBY 2>/dev/null
wait $LOBBY 2>/dev/null

GUESTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/guest_run.log" | head -1)
grep -h -A24 "Menu tour console: > " "$HOSTDIR/measurement.log" | grep -v "^Menu tour: \|^--\|^\[" > "$OUT/host_console.txt"
grep -h -A12 "Menu tour console: > " "$GUESTDIR/measurement.log" | grep -v "^Menu tour: \|^--\|^\[" > "$OUT/guest_console.txt"
echo "session code: $CODE ($MODE)"
grep -h "local \|code \|joined as player\|Connected to the host\|connection(s)\|did not answer\|No path" \
    "$OUT/guest_console.txt" "$OUT/host_console.txt" | sort -u
echo "lobby: $(tail -1 "$OUT/lobby.log")"
