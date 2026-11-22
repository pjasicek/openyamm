# Two machines

Co-op checks over a real network between this PC and a second one. The scripts here start one game on each, drive
both with menu-input tours and bring the results back. The design is in
[the architecture](../../devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md); what is still open is in
[the open items](../../devdocs/plans/MULTIPLAYER_OPEN_ITEMS.md).

## The second PC

- **How to reach it:** `ssh oyamm-nb2`. The alias is in the user's `~/.ssh/config` (key login, no password), not in
  this repository. Another machine can be used by setting `OPENYAMM_PEER=<ssh alias>`.
- **What it is:** a notebook with Ubuntu, the same release as the development PC, so the game built here runs there
  as it is. It has an integrated GPU and is on Wi-Fi.
- **What is on it:** a copy of the built game and its assets in `~/github/OpenYAMM` (the binary, `assets_dev`, the
  settings and the launcher). Nothing is built there and no source is copied.
- **How a game shows there:** in the desktop session that is logged in on the notebook, minimized, through the
  session's X11 display (`DISPLAY=:0` with the session's Xwayland authority file, `SDL_VIDEODRIVER=x11`). On the
  session's Wayland display a window that starts minimized never gets a frame and the game waits for good. The
  session must be logged in and not locked. Vertical sync is off for it (`vblank_mode=0`): a minimized window is
  given one frame a second there otherwise. It then runs at about 40 frames a second on Dagger Wound.
- **Where the copy lies:** at the same path as the checkout on the development PC. The game reads its compiled
  shaders from `build/runtime/` under that path, so `sync.sh` copies that folder too.
- **Agents may install what a check needs** on it (the user, 2026-11-20). Write down here what was installed.
  Installed so far: nothing.
- **Settings changed on it** (2026-11-20, with the user's leave to change its power saving):
  - the session never goes idle (`org.gnome.desktop.session idle-delay` 0, was 3600), so the screen does not
    blank and lock itself and the game keeps a session to show in. Locking by hand still works;
  - Wi-Fi power saving is off (`802-11-wireless.powersave` 2 on its connection, was the default "on"), so the
    radio does not hold packets back. The ping between the two machines is then 1 to 6 ms.
  - Already so before: closing the lid does nothing, and it does not suspend on mains power.

## The public lobby

Every game asks `oylobby.jasicek.net` for the lobby unless its player ticks Local Network Only or types a lobby of
their own (`Coop::DefaultLobbyAddress`). Since 2026-11-21 that name is a small rented server:

- **What it is:** an Oracle Cloud "Always Free" VM (shape `VM.Standard.E2.1.Micro`, x86, 1 GB, Ubuntu 24.04
  minimal) in the Frankfurt region, in the user's Oracle account. Its public address is a reserved one,
  129.159.249.144, and `oylobby.jasicek.net` is an A record for it in the user's DNS at WEDOS (beside a `*`
  record for the home address, which the name would fall back to if the record were deleted).
- **How to reach it:** `ssh -i ~/.ssh/id_ecdsa ubuntu@oylobby.jasicek.net` (key login only; `sudo` without a
  password). In Oracle's console it is the instance `openyamm-lobby` with the network `openyamm-lobby`, the subnet
  `lobby-public`, the gateway `lobby-gateway` and the reserved address `openyamm-lobby`; nothing else was made
  there.
- **The service:** the system service `openyamm-lobby` (the unit of
  [Running your own lobby server](../lobby_server/README.md), installed as
  `/etc/systemd/system/openyamm-lobby.service`), the program `/opt/openyamm-lobby/openyamm_lobby_server`,
  UDP 27910 and sixteen relay ports, 27911 to 27926. It runs as a user that exists only while it runs, with no
  privileges, the system read-only, sockets only on its own ports and no reach into the VM's private network
  (`systemd-analyze security openyamm-lobby`: 1.2). Its log: `sudo journalctl -u openyamm-lobby`.
- **Firewalls:** Oracle's security list of the subnet lets in TCP 22 and UDP 27910 to 27926. The VM's own
  `iptables` (saved in `/etc/iptables/rules.v4`) lets the same UDP ports in after three limits: 20 datagrams a
  second per sender on 27910, 800 a second per sender on the relay ports, 8000 a second in all.
- **To put a new program there** (after `engine/net/Rendezvous*` changed; the game and the lobby must be of one
  build of that code):

  ```sh
  g++ -std=c++20 -O2 -static-pie -fstack-protector-strong -D_FORTIFY_SOURCE=2 -I. -Ibuild/_deps/enet-src/include \
      tools/lobby_server_main.cpp engine/net/ByteStream.cpp engine/net/EnetTransport.cpp \
      engine/net/RendezvousProtocol.cpp engine/net/RendezvousServer.cpp build/libopenyamm_enet.a \
      -o openyamm_lobby_server
  scp -i ~/.ssh/id_ecdsa openyamm_lobby_server ubuntu@oylobby.jasicek.net:/tmp/
  ssh -i ~/.ssh/id_ecdsa ubuntu@oylobby.jasicek.net 'sudo install -m 0755 /tmp/openyamm_lobby_server \
      /opt/openyamm-lobby/ && sudo systemctl restart openyamm-lobby'
  ```

- **Tried on 2026-11-21:** a game here hosted through the name and got its code, a second game here joined by the
  code; the lobby logged the session and the join. Both games were behind one router, so the path between them was
  the local network's: the path through two different routers is still untried (the open items' CO-74).
- **To know:** Oracle may take back an Always Free VM that stays idle, and a lobby is nearly idle. Accounts
  upgraded to "Pay As You Go" are said to be exempt while the free resources stay free; not checked against
  Oracle's terms. If the VM is lost, the same steps make another, and only the DNS record changes.

## The lobby server at home

The lobby service (`openyamm_lobby_server`: the list of sessions, their codes, the path through routers and the
relay) runs on the home server, `ssh server`, 192.168.1.128, for the home network only:

- **Where:** `~/openyamm-lobby/openyamm_lobby_server`, UDP 27910 and the relay's ports 27911 to 27914.
- **Started by:** the user service `openyamm-lobby` (`systemctl --user status openyamm-lobby`,
  `journalctl --user -u openyamm-lobby`), which starts with the machine (lingering is on for the user).
- **In a sandbox** since 2026-11-21 (a user service, `~/.config/systemd/user/openyamm-lobby.service` on that
  machine; the unit from before is beside it as `openyamm-lobby.service.before-hardening`; how such a unit is
  made is in [Running your own lobby server](../lobby_server/README.md)). The service reads datagrams from anyone, so it is given nothing to
  lose: the system is read-only to it, the home folders are empty but for its own folder, the folders that hold
  other data (`/mnt`, `/media`, `/srv`, `/opt`, `/var`, `/container_volumes`, the ssh and network settings) are not
  there for it, it has no privileges, may open only internet sockets, and is held to 256 MB, 16 tasks and half a
  processor. `systemd-analyze --user security openyamm-lobby` rates it 1.9 (it was 9.8). What it sees can be looked
  at from outside: `ls /proc/$(systemctl --user show -p MainPID --value openyamm-lobby)/root/home/$USER` lists only
  `openyamm-lobby`. A new data folder at the top of the disk has to be added to the unit's `InaccessiblePaths`.
- **Firewall:** `ufw` lets UDP 27910 to 27914 in from everywhere since 2026-11-20 (the rule "OpenYAMM co-op
  lobby"; the earlier rule for 192.168.1.0/24 is still there and harmless).
- **Not reachable from outside yet:** the home's router does not pass those UDP ports on to this machine. With
  UDP 27910 to 27914 forwarded to 192.168.1.128, the lobby is public at the home's public name; then that name
  goes into `GameSettings::coopLobbyAddress` as the built-in default, and nobody types a lobby's address.
- **What it refuses:** an address that asks more than ten times a second on the average (forty at once) is not
  answered until it slows down. A relayed pair may send 512 kB a second.
- **The program there is the same static build as the public lobby's** (the command above; that machine's
  Ubuntu is older than the development PC's), put there with
  `scp openyamm_lobby_server server:openyamm-lobby/ && ssh server 'systemctl --user restart openyamm-lobby'`. It
  needs that again when `engine/net/Rendezvous*` changes: a game and a lobby of different builds of that code do
  not understand each other. Updated on 2026-11-21 (the program from before is beside it as
  `openyamm_lobby_server.v1`). Games use it only when its address is typed as the player's own lobby.
- **To remove it:** `systemctl --user disable --now openyamm-lobby`, delete the folder and the unit
  (`~/.config/systemd/user/openyamm-lobby.service`), and delete the two `ufw` rules for 27910:27914/udp
  (`sudo ufw status numbered`, then `sudo ufw delete <number>`).

A game uses it once its address is typed on the Multiplayer screen (it is remembered after that).

## The scripts

| Script | What it does |
| --- | --- |
| `sync.sh` | Copies the built game, the assets, the settings and the launcher to the second PC. Run it after every build that is to be tested: the host refuses a game of another build or other content |
| `run.sh [mode] [seconds]` | Starts the two games, lets them play together for `seconds` (40 by default) and prints what happened |

`run_screens.sh [lobby address]` drives the Multiplayer screen by clicks on both PCs: this PC hosts with the
lobby's address typed in and copies its code, the second PC opens Join and joins with one click on the game
listed. It captures every screen into `output/coop_two_machines/screens/`.

`run.sh` modes:

| Mode | Host | How the other joins |
| --- | --- | --- |
| `host-here` (default) | this PC | by this PC's address |
| `host-there` | the second PC | this PC scans the network, then joins the address found |
| `lobby` | this PC, with the lobby service here | by the session's code, over a direct path |
| `lobby-relay` | the same | by the code, through the lobby's relay only |

`run.sh session [seconds]` is a played session rather than a join: this PC hosts, and the two games act in step
(their tours wait for the same moments of the wall clock, the tour step `wait_until`):

| Beat | What happens | What must agree afterwards |
| --- | --- | --- |
| start | the guest stands opposite the host | both characters' places and health |
| fight | the host spawns four pirates between them; both strike for `seconds` (30 by default) | the pirates left, killed and in all |
| loot | the host drops a sword at the guest's feet; the guest looks down and picks up what is there | the guest's bags and gold |
| down | the host strikes the guest down | the guest is down in both games, with its gold |
| back | fifteen seconds later the guest presses Use | it stands at the arrival point, its gold gone |
| rest | the guest asks for eight hours' rest, the host agrees | the clock, eight hours on |
| travel | the host goes to Ravenshore (the console's `goto`, which asks no vote) | the map, both places, the clock |

At each beat both games print their state (`coop show`, `coop net`, `actor count`, `time`, `coop check`), and
`compare_states.py` prints one line per beat: `same`, or what differs. The guest is player 1 in the host's game
and player 0 in its own.

Two settings of the environment:

- `OPENYAMM_PEER=local` runs both games on this PC (output in `output/coop_two_machines/local-<mode>/`). It is
  the quick way to work on a session: over one home network the two PCs show nothing localhost does not, except
  the second machine's speed.
- `OPENYAMM_BAD_LINE="delay 100ms 40ms loss 10%"` puts that on the second PC's side of the game's UDP, in both
  directions, for the run (`tc netem`, which needs root there; ssh is left as it is). The run prints netem's
  counters when it takes the line down again.

The results are in `output/coop_two_machines/<mode>/`: both games' console lines, the lobby's log, and screenshots
of each game seeing the other.

## What a run does

1. The host's game starts and hosts. The script waits until it listens (or until the lobby gave it a code).
2. The joining game lists what it finds (`coop find`), joins, stands in front of the host, says a line, strikes
   twice and walks from side to side.
3. The host says a line, points at a place and takes two screenshots.
4. Both print `coop net` (the connection and the traffic) and `coop chat` at the end.

## Results of 2026-11-20

All four modes, forty seconds of play each, the second PC on 2.4 GHz Wi-Fi (ping 1 to 6 ms):

| Mode | Joined | Path | The guest received | The guest sent |
| --- | --- | --- | --- | --- |
| `host-here` | yes; the scan listed the host | by address | 2.3 MB | 82 kB |
| `host-there` | yes; the scan listed the host | by address | 2.2 MB | 81 kB |
| `lobby` | yes, by code | direct; nothing relayed | 2.4 MB | 82 kB |
| `lobby-relay` | yes, by code | relay; 5216 datagrams, 2.5 MB, none dropped | 2.2 MB | 80 kB |

The counts are from the join to the guest's last line, about fifty seconds. The first 0.55 MB is the world on
joining; after it the host sends a guest roughly 45 kB a second on Dagger Wound (108 monsters) and the guest sends
about 2 kB a second. Both chat lines arrived on both sides in every run, the guest was still in the
session at its last line, and the host saw it leave. The screenshots show each game drawing the other's body with
its name, the players panel and the chat. The development PC ran at 58 frames a second or more, the notebook at
about 43.

### The session, 2026-11-20

Twenty seconds of fighting, the guest on the notebook. "Agreed" means `compare_states.py` printed `same`.

As it stands at the end of the day (packed messages, the transport's two changes, the host-given pickup):

| Line | Runs | Result |
| --- | --- | --- |
| both games on this PC | 1 | agreed at all seven beats |
| two PCs, clean | 2 | agreed at all seven beats; the guest received about 2.6 MB and sent 0.14 MB in some four minutes |
| two PCs, 100 ms ± 40 ms, 10 % loss | 5 | the map change arrived in time in all five. Four runs showed the rest's beat as differing, which was the tour's fault (its clock stood during the rest, so the guest printed late); with that mended the one run since agreed at all seven beats |

What the session found on the way, all closed the same day (the open items' CO-85 to CO-91):

- a guest struck down ran the single-player defeat in its own game;
- on the clean line the guest dropped out at the map change (the transport gave it up after five silent seconds);
- on the very bad line the map change took between 40 and 140 seconds to arrive (some 200 packets, and a lost
  one's wait doubling without a limit);
- an item the guest picked up still lay in the host's world.

Earlier the same day, before packing: the clean line and 60 ms ± 20 ms with 2 % loss agreed at all seven beats,
with about 6.3 MB received by the guest.

### At the end of 2026-11-20

The session agreed at all seven beats on the clean line with the last build of the day (protocol 7: password,
packed messages, the comparison of gameplay data, the host-given pickup), and `run_screens.sh` went from the
title menu to a joined guest by clicks through the home lobby. One run before it was refused by the host: the
two trees' gameplay scripts differed, another session having changed some between the copy and the run. Both
scripts now copy the tables and scripts again just before they start.

## Limits

- Both machines are on one home network, so no router is between them. The lobby's hole punch through real routers
  is still unproven.
- The first copy of the assets takes about forty minutes over the notebook's Wi-Fi (12 GB); later ones copy only
  what changed.
