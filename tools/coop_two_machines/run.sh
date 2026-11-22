#!/bin/bash
# Two real games over a real network: one on this PC, one on the second PC (ssh alias oyamm-nb2, README.md).
# Each game is driven by a menu-input tour; the other one runs inside the second PC's desktop session.
#   tools/coop_two_machines/run.sh [mode] [seconds]
#     host-here    this PC hosts, the second PC joins by this PC's address               (default)
#     host-there   the second PC hosts, this PC finds it by a scan of the network and joins it
#     lobby        the lobby service and the host here; the second PC joins by the session's code
#     lobby-relay  the same through the lobby's relay only
#     session      this PC hosts and the two play: a fight, loot, a death and a return, a rest, a map change
#   seconds: how long the two play together (default 40); for `session`, how long the fights go on (default 30).
# OPENYAMM_PEER=<ssh alias> names another second PC; OPENYAMM_PEER=local runs both games on this PC.
# OPENYAMM_BAD_LINE="delay 100ms 40ms loss 10%" puts that on the second PC's side of the game's traffic (tc netem,
# both directions of its UDP; needs root there) for the run.
# Run tools/coop_two_machines/sync.sh first, after every build.
# Output: output/coop_two_machines/<mode>/ (both games' console lines and screenshots, a summary on the terminal).
set -u
MODE="${1:-host-here}"
PLAY="${2:-40}"
PEER="${OPENYAMM_PEER:-oyamm-nb2}"
BAD_LINE="${OPENYAMM_BAD_LINE:-}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOBBY_PORT=27910
GAME_PORT=27950
cd "$ROOT" || exit 1

case "$MODE" in
host-here|host-there|lobby|lobby-relay|session) ;;
*)
    echo "usage: run.sh [host-here | host-there | lobby | lobby-relay | session] [seconds]"
    exit 2
    ;;
esac

# Where the other game runs and how it is reached.
if [ "$PEER" = local ]; then
    OUT="$ROOT/output/coop_two_machines/local-$MODE"
    THERE_ROOT="$ROOT"
    THERE_OUT="$OUT/there"
    HERE_IP=127.0.0.1
    PEER_IP=127.0.0.1
    there() { bash -c "$1"; }
    put() { cp "$1" "$2"; }
else
    OUT="$ROOT/output/coop_two_machines/$MODE"
    ssh "$PEER" true || { echo "cannot reach $PEER"; exit 1; }
    THERE_ROOT="$(ssh "$PEER" 'echo $HOME')/github/OpenYAMM"
    THERE_OUT="$THERE_ROOT/output/coop_two_machines/$MODE"
    PEER_IP=$(ssh "$PEER" "hostname -I | cut -d' ' -f1")
    HERE_IP=$(ip route get "$PEER_IP" | sed -n 's/.* src \([0-9.]*\).*/\1/p')
    there() { ssh "$PEER" "$1"; }
    put() { scp -q "$1" "$PEER:$2"; }
    if [ "$(sha256sum build/game/openyamm | cut -c1-16)" != "$(there "sha256sum $THERE_ROOT/build/game/openyamm | cut -c1-16")" ]; then
        echo "the second PC has another build: run tools/coop_two_machines/sync.sh first"
        exit 1
    fi
fi
mkdir -p "$OUT"
there "mkdir -p $THERE_OUT"

if [ "$PEER" != local ]; then
    # The gameplay tables and scripts once more, just before the games start: a host refuses a game whose copies
    # differ, and in a tree other sessions work in they change by the minute (sync.sh copies everything else).
    rsync -a --delete assets_dev/engine/data_tables assets_dev/engine/events assets_dev/engine/rulesets \
        "$PEER":github/OpenYAMM/assets_dev/engine/
    for world in assets_dev/worlds/*/; do
        [ -d "$world/events" ] && rsync -a --delete "$world/events" "$PEER":github/OpenYAMM/"$world"
    done
fi
echo "this PC $HERE_IP, the other game on $PEER_IP ($PEER), mode $MODE${BAD_LINE:+, bad line: $BAD_LINE}"

# ---------------------------------------------------------------------------------------------------------------
# The bad line: netem on the second PC's network device for the game's UDP only, so that ssh stays as it is.

bad_line_on() {
    [ -z "$BAD_LINE" ] && return
    if [ "$PEER" = local ]; then
        echo "a bad line needs a second PC (netem on its network device)"
        exit 1
    fi
    # Outgoing: a prio band with netem, chosen for UDP to or from the game's port. Incoming: the same through an
    # ifb device, since netem shapes only what leaves.
    there "dev=\$(ip route get $HERE_IP | sed -n 's/.* dev \([^ ]*\).*/\1/p');
        sudo -n modprobe ifb numifbs=1 && sudo -n ip link set ifb0 up &&
        for d in \$dev ifb0; do
            sudo -n tc qdisc replace dev \$d root handle 1: prio &&
            sudo -n tc qdisc replace dev \$d parent 1:3 handle 30: netem $BAD_LINE &&
            sudo -n tc filter replace dev \$d protocol ip parent 1: prio 1 u32 match ip protocol 17 0xff \
                match ip dport $GAME_PORT 0xffff flowid 1:3 &&
            sudo -n tc filter replace dev \$d protocol ip parent 1: prio 2 u32 match ip protocol 17 0xff \
                match ip sport $GAME_PORT 0xffff flowid 1:3;
        done &&
        sudo -n tc qdisc replace dev \$dev handle ffff: ingress &&
        sudo -n tc filter replace dev \$dev parent ffff: protocol ip u32 match ip protocol 17 0xff \
            action mirred egress redirect dev ifb0 && echo 'bad line on'" || { bad_line_off; exit 1; }
}

bad_line_off() {
    [ -z "$BAD_LINE" ] && return
    [ "$PEER" = local ] && return
    there "dev=\$(ip route get $HERE_IP | sed -n 's/.* dev \([^ ]*\).*/\1/p');
        sudo -n tc -s qdisc show dev \$dev | grep -A2 netem | tr '\n' ' '; echo;
        sudo -n tc qdisc del dev \$dev root 2>/dev/null; sudo -n tc qdisc del dev \$dev ingress 2>/dev/null;
        sudo -n tc qdisc del dev ifb0 root 2>/dev/null; sudo -n ip link set ifb0 down 2>/dev/null; echo 'bad line off'"
}

LOBBY=""
cleanup() {
    bad_line_off
    [ -n "$LOBBY" ] && kill "$LOBBY" 2>/dev/null
}
trap cleanup EXIT

# ---------------------------------------------------------------------------------------------------------------
# The tours.

# What the guest does once it is in: looks at the host, says a line, strikes, walks from side to side.
guest_play() {
    cat <<TOUR
  - console: coop net
  - console: tp 3560 8200 600 -1.5708 0
  - wait: 2
  - capture: guest-sees-host
  - console: coop say Hello from the other machine
  - wait: 2
  - action: attack
  - wait: 1
  - action: attack
  - wait: 1
TOUR
    for _ in $(seq 1 $((PLAY / 2))); do
        printf '  - action_down: left\n  - wait: 0.8\n  - action_up: left\n  - action_down: right\n  - wait: 0.8\n  - action_up: right\n'
    done
    printf '  - console: coop net\n  - console: coop chat\n  - wait: 2\n'
}

# What the host does while the guest plays. It stays well past the guest's last line, so that the guest's closing
# `coop net` still shows a session.
host_play() {
    cat <<TOUR
  - console: coop net
  - console: coop show
  - console: coop say Welcome
  - console: coop ping 3560 8000 545
  - wait: 1
  - capture: host-sees-guest
  - wait: $((PLAY / 2))
  - capture: host-sees-guest-later
  - wait: $((PLAY / 2 + 45))
  - console: coop net
  - console: coop chat
  - console: coop show
  - wait: 3
TOUR
}

# The session: both tours wait for the same moments of the wall clock (T0 and so many seconds after it), so the two
# games act beat for beat however long each took to start. `state` prints what the two games are compared by.
at() { printf '  - wait_until: %s\n' $((T0 + $1)); }

state() {   # state <host|guest> <label>: the guest is player 1 in the host's game and player 0 in its own
    local guest=1
    [ "$1" = guest ] && guest=0
    printf '  - console: coop say %s at %s\n  - console: coop show\n  - console: coop net\n' "$1" "$2"
    printf '  - console: actor count 181\n  - console: time\n'
    for field in bag_items down gold hp; do
        printf '  - console: coop check %s %s >= 0\n' "$guest" "$field"
    done
}

strikes() {   # strikes <seconds>: an Attack about each second (a tour step takes 0.35 s itself)
    for _ in $(seq 1 "$1"); do printf '  - action: attack\n  - wait: 0.65\n'; done
}

session_host() {
    local F=$((8 + PLAY))
    cat <<TOUR
$(at 0)
$(state host start)
$(at 6)
  - console: actor spawn 181 4 3560 8050 545
$(at 8)
  - capture: host-fight
$(strikes "$PLAY")
$(at $((F + 2)))
  - console: actor kill 900
$(at $((F + 5)))
$(state host after-fight)
$(at $((F + 11)))
  - console: item drop 1 3560 8250 545
$(at $((F + 20)))
$(state host after-loot)
$(at $((F + 26)))
  - console: coop damage 1 100000
$(at $((F + 30)))
$(state host guest-down)
  - capture: host-sees-guest-down
$(at $((F + 46)))
$(state host guest-back)
$(at $((F + 56)))
  - console: coop rest
  - console: coop rest 0 yes
$(at $((F + 82)))
$(state host after-rest)
$(at $((F + 88)))
  - console: goto 2
$(at $((F + 128)))
$(state host after-travel)
  - capture: host-new-map
  - console: coop chat
$(at $((F + 147)))
TOUR
}

session_guest() {
    local F=$((8 + PLAY))
    cat <<TOUR
  - console: tp 3560 8400 600 -1.5708 0
$(at 0)
$(state guest start)
$(at 8)
  - capture: guest-fight
$(strikes "$PLAY")
$(at $((F + 5)))
$(state guest after-fight)
$(at $((F + 13)))
  - console: tp 3560 8400 600 -1.5708 -45
  - wait: 1.5
  - capture: guest-sees-item
  - action: trigger
  - wait: 1
  - console: tp 3560 8400 600 -1.5708 0
$(at $((F + 20)))
$(state guest after-loot)
$(at $((F + 30)))
$(state guest guest-down)
  - capture: guest-down
$(at $((F + 41)))
  - action: use
$(at $((F + 46)))
$(state guest guest-back)
$(at $((F + 53)))
  - console: rest heal 480
  - wait: 1
  - console: coop rest
$(at $((F + 82)))
$(state guest after-rest)
$(at $((F + 128)))
$(state guest after-travel)
  - capture: guest-new-map
  - console: coop chat
$(at $((F + 134)))
TOUR
}

tour() {   # tour <file> <capture dir> <steps...>
    local file="$1" dir="$2"
    shift 2
    { printf 'output_dir: %s\nexit: true\nsteps:\n  - wait: 1\n' "$dir"; printf '%s\n' "$@"; } > "$file"
}

run_here() {   # run_here <name> <map> <seconds> <tour file> <log>
    SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "$1" --world mm8 --map "$2" \
        --position 3560 7696 545 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds "$3" \
        --set debug.menu_input_tour_path="$4" > "$5" 2>&1
}

run_there() {  # run_there <name> <map> <seconds> <tour file on the second PC> <log>
    if [ "$PEER" = local ]; then
        run_here "$@"
        return
    fi
    # In the desktop session logged in there, through its X11 display: on its Wayland display a window that starts
    # minimized never gets a frame, and the game waits for one for good.
    # Without vertical sync (vblank_mode=0): a minimized window is given one frame a second there otherwise.
    ssh "$PEER" "cd $THERE_ROOT && XDG_RUNTIME_DIR=/run/user/\$(id -u) DISPLAY=:0 \
        XAUTHORITY=\$(ls /run/user/\$(id -u)/.mutter-Xwaylandauth.* | head -1) SDL_VIDEODRIVER=x11 \
        vblank_mode=0 SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated $1 --world mm8 --map $2 \
        --position 3560 7696 545 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds $3 \
        --set debug.menu_input_tour_path=$4" > "$5" 2>&1
}

run_dir() { sed -n 's/^Isolated run: //p' "$1" 2>/dev/null | head -1; }

console_lines() {   # console_lines <run log> <here|there> > file
    local dir
    dir=$(run_dir "$1")
    if [ "$2" = "here" ]; then
        grep -a -h -A24 "Menu tour console: > " "$dir/measurement.log"
    else
        there "grep -a -h -A24 'Menu tour console: > ' '$dir/measurement.log'"
    fi | grep -v "^Menu tour: \|^--\|^\[" | sed 's/^Menu tour console: //'
}

# Waits until a game's log has a line; fails when the game ends first.
wait_for_line() {   # wait_for_line <here|there> <run log> <pattern> <pid of the game's launcher>
    local dir
    for _ in $(seq 1 180); do
        dir=$(run_dir "$2")
        if [ -n "$dir" ]; then
            if [ "$1" = here ]; then
                grep -a -qs "$3" "$dir/openyamm.log" "$dir/measurement.log" && return 0
            else
                there "grep -a -qs '$3' '$dir/openyamm.log' '$dir/measurement.log'" && return 0
            fi
        fi
        kill -0 "$4" 2>/dev/null || { echo "a game ended before '$3'; see $2"; return 1; }
        sleep 1
    done
    echo "no '$3' after three minutes; see $2"
    return 1
}

# ---------------------------------------------------------------------------------------------------------------
# The run.

HOST_WHERE=here
GUEST_WHERE=there
HOST_TOTAL=$((PLAY + 130))
GUEST_TOTAL=$((PLAY + 50))
HOST_STEPS="$(host_play)"
GUEST_STEPS="$(guest_play)"
HOST_LINE="coop host"
HOST_LEAD=22
[ "$MODE" = host-there ] && { HOST_WHERE=there; GUEST_WHERE=here; }
if [ "$MODE" = session ]; then
    # The moment both tours begin to play: by then the host is up and the guest has started, loaded and joined.
    LEAD=80
    [ "$PEER" = local ] && LEAD=50
    T0=$(( $(date +%s) + LEAD ))
    HOST_TOTAL=$((PLAY + LEAD + 190))
    GUEST_TOTAL=$((PLAY + LEAD + 175))
    HOST_STEPS="$(session_host)"
    GUEST_STEPS="$(session_guest)"
    HOST_LEAD=0
fi
if [ "$MODE" = lobby ] || [ "$MODE" = lobby-relay ]; then
    ./build/tools/openyamm_lobby_server --port $LOBBY_PORT --relay-ports 4 > "$OUT/lobby.log" 2>&1 &
    LOBBY=$!
    sleep 1
    HOST_LINE="coop host lobby $HERE_IP:$LOBBY_PORT The two machines"
fi

bad_line_on

if [ "$HOST_WHERE" = here ]; then
    HOST_CAPTURES="$OUT"; HOST_TOUR="$OUT/host_tour.yml"
    GUEST_CAPTURES="$THERE_OUT"; GUEST_TOUR="$THERE_OUT/guest_tour.yml"
    HOST_IP="$HERE_IP"
else
    HOST_CAPTURES="$THERE_OUT"; HOST_TOUR="$THERE_OUT/host_tour.yml"
    GUEST_CAPTURES="$OUT"; GUEST_TOUR="$OUT/guest_tour.yml"
    HOST_IP="$PEER_IP"
fi

tour "$OUT/host_tour.yml" "$HOST_CAPTURES" "  - console: $HOST_LINE" "  - wait: 3" "  - console: coop net" \
    "  - wait: $HOST_LEAD" "$HOST_STEPS"
[ "$HOST_WHERE" = there ] && put "$OUT/host_tour.yml" "$HOST_TOUR"
if [ "$HOST_WHERE" = here ]; then
    run_here coop2m_host out01.odm "$HOST_TOTAL" "$HOST_TOUR" "$OUT/host_run.log" &
else
    run_there coop2m_host out01.odm "$HOST_TOTAL" "$HOST_TOUR" "$OUT/host_run.log" &
fi
HOST=$!
wait_for_line "$HOST_WHERE" "$OUT/host_run.log" "hosting on UDP" $HOST || exit 1

JOIN="coop join $HOST_IP"
if [ -n "$LOBBY" ]; then
    wait_for_line here "$OUT/host_run.log" "lobby code " $HOST || exit 1
    HOSTDIR=$(run_dir "$OUT/host_run.log")
    CODE=$(grep -a -hs -o "lobby code [A-Z0-9]*" "$HOSTDIR/openyamm.log" "$HOSTDIR/measurement.log" | head -1 | sed 's/lobby code //')
    [ "$MODE" = lobby ] && JOIN="coop join code $CODE $HERE_IP:$LOBBY_PORT"
    [ "$MODE" = lobby-relay ] && JOIN="coop join relay $CODE $HERE_IP:$LOBBY_PORT"
fi

tour "$OUT/guest_tour.yml" "$GUEST_CAPTURES" "  - console: coop find${LOBBY:+ $HERE_IP:$LOBBY_PORT}" \
    "  - console: $JOIN" "  - wait: 8" "$GUEST_STEPS"
[ "$GUEST_WHERE" = there ] && put "$OUT/guest_tour.yml" "$GUEST_TOUR"
if [ "$GUEST_WHERE" = here ]; then
    run_here coop2m_guest out02.odm "$GUEST_TOTAL" "$GUEST_TOUR" "$OUT/guest_run.log"
else
    run_there coop2m_guest out02.odm "$GUEST_TOTAL" "$GUEST_TOUR" "$OUT/guest_run.log"
fi
while kill -0 $HOST 2>/dev/null; do sleep 1; done

console_lines "$OUT/host_run.log" "$HOST_WHERE" > "$OUT/host_console.txt"
console_lines "$OUT/guest_run.log" "$GUEST_WHERE" > "$OUT/guest_console.txt"
[ -n "$LOBBY" ] && { kill $LOBBY 2>/dev/null; wait $LOBBY 2>/dev/null; }
# The screenshots the other game took.
if [ "$PEER" = local ]; then
    cp "$THERE_OUT"/*.png "$OUT/" 2>/dev/null
else
    rsync -aq "$PEER:$THERE_OUT/"'*.png' "$OUT/" 2>/dev/null
fi

# ---------------------------------------------------------------------------------------------------------------
# The summary.

echo "--- what the joining game found and how it joined"
grep "^local \|^code \|joined as player\|Connected to the host\|refused\|did not answer\|No path\|was lost" "$OUT/guest_console.txt" | sort -u
echo "--- the host"
grep "connection(s)" "$OUT/host_console.txt" | sed -n 2p
grep "^player 1 at\|left the game" "$OUT/host_console.txt" | sort -u | head -4
echo "--- traffic as the guest counted it"
grep "^sent .* messages" "$OUT/guest_console.txt" | tail -1
echo "--- the line as each game measured it, first and last"
grep -h "^line to " "$OUT/host_console.txt" | sed -n '1p;$p'
grep -h "^line to " "$OUT/guest_console.txt" | sed -n '1p;$p'
echo "--- the guest at its last line"
grep "^joined as player\|^no network session" "$OUT/guest_console.txt" | tail -1
fps() { grep -h -o "Average FPS (last second): [0-9]*" "$1" | tail -10 | sed 's/.*: //' | sort -n | sed -n 5p; }
echo "--- frames a second, last ten seconds: host $(fps "$OUT/host_console.txt"), guest $(fps "$OUT/guest_console.txt")"
[ -n "$LOBBY" ] && echo "--- lobby: $(tail -1 "$OUT/lobby.log")"

if [ "$MODE" = session ]; then
    # Each state block of the two games, side by side: what differs is printed.
    echo "--- the two games' state at each beat (a line is printed where they differ)"
    python3 "$ROOT/tools/coop_two_machines/compare_states.py" "$OUT/host_console.txt" "$OUT/guest_console.txt"
else
    said() {
        sed 's/[[:space:]]*$//' "$1" | grep -x "[A-Za-z]*: \(Welcome\|Hello from the other machine\)" | sort -u | wc -l
    }
    echo "--- said and heard: the host's chat has $(said "$OUT/host_console.txt") of the 2 lines, the guest's $(said "$OUT/guest_console.txt")"
fi
echo "output: $OUT"
