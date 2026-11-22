#!/bin/bash
# The Multiplayer screen by clicks, on two PCs: this PC starts at the title menu, chooses Multiplayer there (which
# continues the latest game and opens the screen), hosts with a lobby server's address typed in and copies the
# invitation; the second PC (README.md) opens Join, types the lobby's address and joins with one
# click on the game listed. Captures of every screen go to output/coop_two_machines/screens/.
#   tools/coop_two_machines/run_screens.sh [lobby address]      (default: the home lobby, README.md)
# The clicks are in the menu's 1600 x 900 design coordinates (tools/RUN_GAME.md); a control that moves in
# game/ui/screens/CoopMenuScreen.cpp needs its click moved here.
set -u
LOBBY="${1:-192.168.1.128}"
PEER="${OPENYAMM_PEER:-oyamm-nb2}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/output/coop_two_machines/screens"
cd "$ROOT" || exit 1
mkdir -p "$OUT"
THERE_ROOT="$(ssh "$PEER" 'echo $HOME')/github/OpenYAMM"
THERE_OUT="$THERE_ROOT/output/coop_two_machines/screens"
ssh "$PEER" "mkdir -p $THERE_OUT"

# The gameplay tables and scripts once more, just before the games start: a host refuses a game whose copies
# differ, and in a tree other sessions work in they change by the minute (sync.sh copies everything else).
rsync -a --delete assets_dev/engine/data_tables assets_dev/engine/events assets_dev/engine/rulesets \
    "$PEER":github/OpenYAMM/assets_dev/engine/
for world in assets_dev/worlds/*/; do
    [ -d "$world/events" ] && rsync -a --delete "$world/events" "$PEER":github/OpenYAMM/"$world"
done
STARTED=$(date +%s)
cat > "$OUT/host_tour.yml" <<TOUR
output_dir: $OUT
exit: true
steps:
  - wait: 2
  - capture: 1-title-menu
  - click: [1273, 626]       # Multiplayer, on the title menu: continues the latest game and opens the screen
  - wait: 12
  - click: [292, 195]        # the Host tab
  - wait: 0.5
  - click: [480, 397]        # the lobby server's field
  - wait: 0.5
  - text: $LOBBY
  - key: Return
  - wait: 0.5
  - capture: 2-host-tab
  - click: [386, 562]        # Host This Game
  - wait: 3
  - capture: 3-hosting
  - click: [358, 345]        # Copy Invitation
  - wait: 1
  - capture: 4-invitation-copied
  - click: [583, 814]        # Return to Game
  - wait: 40
  - console: menu
  - wait: 1
  - click: [800, 469]
  - wait: 1
  - capture: 5-hosting-with-guest
  - console: coop net
  - wait: 15
TOUR
cat > "$OUT/guest_tour.yml" <<TOUR
output_dir: $THERE_OUT
exit: true
steps:
  - wait: 2
  - console: menu
  - wait: 1
  - click: [800, 469]        # Multiplayer
  - wait: 1
  - click: [529, 195]        # the Join tab
  - wait: 1
  - capture: 6-join-tab-no-lobby
  - click: [414, 532]        # the lobby server's field
  - wait: 0.5
  - text: $LOBBY
  - key: Return
  - wait: 3
  - capture: 7-join-tab-games
  - click: [1043, 298]       # the first game found
  - wait: 10
  - capture: 8-joined
  - console: coop net
  - console: menu
  - wait: 1
  - click: [800, 469]
  - wait: 1
  - capture: 9-guest-session
  - wait: 40
TOUR
scp -q "$OUT/guest_tour.yml" "$PEER:$THERE_OUT/guest_tour.yml"

SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_scr_host --menu --world mm8 --map out01.odm \
    --seconds 110 \
    --set debug.menu_input_tour_path="$OUT/host_tour.yml" > "$OUT/host_run.log" 2>&1 &
HOST=$!
# The guest starts once the host's screen says it hosts (its capture of that screen was written in this run).
for _ in $(seq 1 120); do
    [ "$(stat -c %Y "$OUT/3-hosting.png" 2>/dev/null || echo 0)" -ge "$STARTED" ] && break
    kill -0 $HOST 2>/dev/null || { echo "the host ended before it hosted; see $OUT/host_run.log"; exit 1; }
    sleep 1
done
HOSTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/host_run.log" 2>/dev/null | head -1)
ssh "$PEER" "cd $THERE_ROOT && XDG_RUNTIME_DIR=/run/user/\$(id -u) DISPLAY=:0 \
    XAUTHORITY=\$(ls /run/user/\$(id -u)/.mutter-Xwaylandauth.* | head -1) SDL_VIDEODRIVER=x11 \
    vblank_mode=0 SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated coop_scr_guest --world mm8 --map out02.odm \
    --warmup 3 --seconds 95 --set debug.menu_input_tour_path=$THERE_OUT/guest_tour.yml" > "$OUT/guest_run.log" 2>&1
while kill -0 $HOST 2>/dev/null; do sleep 1; done
rsync -aq "$PEER:$THERE_OUT/"'*.png' "$OUT/"
GUESTDIR=$(sed -n 's/^Isolated run: //p' "$OUT/guest_run.log" | head -1)
echo "--- the host"
grep -a -A2 "Menu tour console: > coop net" "$HOSTDIR/measurement.log" | sed 's/^Menu tour console: //' | sed -n 2,3p
echo "--- the guest"
ssh "$PEER" "grep -a -h 'joined as player\|The host refused\|no network session' '$GUESTDIR/measurement.log'" | sed 's/^Menu tour console: //' | sort -u
echo "--- remembered by the host's game"
grep -a -A4 "^\[coop\]" "$HOSTDIR/settings.ini" | grep "="
echo "captures: $OUT"
