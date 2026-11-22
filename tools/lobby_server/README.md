# Running your own lobby server

For someone (or their agent) who wants to run a lobby for OpenYAMM's co-op games. The game already asks a public
lobby by default; you need your own only if you want one under your control, or the public one is gone.

## What the lobby does

A lobby is a small UDP service (`openyamm_lobby_server`, source `tools/lobby_server_main.cpp` and
`engine/net/Rendezvous*`). It keeps nothing of a game:

- a hosting game registers there and gets a short code;
- a joining game asks for the list of games or names a code;
- the lobby tells the two games each other's addresses, so that they open a path through their routers and then
  talk to each other directly;
- when no direct path opens, the lobby relays their traffic through one of its relay ports.

So almost no traffic passes through it, except for pairs it has to relay (roughly 50 kB a second per relayed
guest; each relayed pair is held to about 512 kB a second).

## What you need

- A Linux machine with a public IPv4 address that players can reach (a small rented server is enough: the service
  uses a few megabytes of memory and next to no processor).
- UDP port 27910 and the relay ports after it open to the internet: 27911 to 27926 with the default sixteen relay
  ports. UDP, not TCP. On a rented server there are usually two firewalls to open: the provider's and the
  machine's own.
- The lobby and the games must be built from the same version of the lobby code (`RendezvousVersion` in
  `engine/net/RendezvousProtocol.h`). A game of another version gets no answer. Build the lobby from the same
  release or commit as the games that will use it, and build it again when that code changes.

## Build

From a checkout that has been configured once (`cmake -B build`):

```sh
cmake --build build --target openyamm_lobby_server -j8      # the program: build/tools/openyamm_lobby_server
```

That program needs the build machine's libraries. For a server with another or older system, build one static
file instead and copy that:

```sh
cmake --build build --target openyamm_enet -j8              # the network library the lobby links
g++ -std=c++20 -O2 -static-pie -fstack-protector-strong -D_FORTIFY_SOURCE=2 -I. -Ibuild/_deps/enet-src/include \
    tools/lobby_server_main.cpp engine/net/ByteStream.cpp engine/net/EnetTransport.cpp \
    engine/net/RendezvousProtocol.cpp engine/net/RendezvousServer.cpp build/libopenyamm_enet.a \
    -o openyamm_lobby_server
```

The linker warns about `getaddrinfo` in a static program; the lobby never looks a name up, so the warning does not
matter.

## Run

```sh
./openyamm_lobby_server [--port 27910] [--relay-ports 16] [--quiet] [--relay-lan-with-internet]
```

- `--port`: the lobby's port. The relay ports are the ones right after it.
- `--relay-ports`: how many pairs can be relayed at once. 0 turns the relay off: players whose routers allow no
  direct path then cannot join each other.
- `--quiet`: no log lines for sessions and joins.
- `--relay-lan-with-internet`: only for a lobby on a home network whose own machines also play. Without it the
  lobby does not relay between an address of its own private network and an address on the internet, so that it
  cannot be used to reach into that network.

It logs to standard output: one line when it starts ("lobby on UDP 27910, relay ports ..."), one per session opened
or timed out, one per join.

## Install as a service

The service reads datagrams from anyone on the internet, so do not run it as root or as your own user without a
sandbox. [openyamm-lobby.service](openyamm-lobby.service) runs it as a user that exists only while it runs, with
the system read-only, no privileges, sockets only on its own ports and no reach into the machine's private
network:

```sh
sudo mkdir -p /opt/openyamm-lobby
sudo install -m 0755 openyamm_lobby_server /opt/openyamm-lobby/
sudo install -m 0644 tools/lobby_server/openyamm-lobby.service /etc/systemd/system/openyamm-lobby.service
sudo systemctl daemon-reload
sudo systemctl enable --now openyamm-lobby
systemctl is-active openyamm-lobby            # active
sudo journalctl -u openyamm-lobby -n 5        # "lobby on UDP 27910, relay ports 27911 to 27926"
sudo ss -ulnp | grep -c 279                   # 17 sockets with sixteen relay ports
systemd-analyze security openyamm-lobby       # about 1.2
```

With another port or number of relay ports, change `ExecStart` and `SocketBindAllow` in the unit together. The unit
needs systemd 249 or newer for `SocketBindAllow`; on an older one remove the two `SocketBind` lines.

Without root (a user service on a home machine), most of the same directives work when the unit also has
`PrivateUsers=yes`; use `ProtectHome=tmpfs` with `BindReadOnlyPaths=` for the program's folder, drop `DynamicUser`,
`SocketBind*` and `IPAddressDeny`, and check what the process can see with
`ls /proc/<its pid>/root/home/<you>`. An empty root (`TemporaryFileSystem=/`) does not take effect in a user service
of systemd 249: the process sees the whole disk.

## Firewall

Open the ports, and if you can, limit how fast one sender may ask. With `iptables` (rules before the final
reject or drop of the INPUT chain; save them with `netfilter-persistent save` or your system's way):

```sh
iptables -A INPUT -p udp --dport 27910 -m hashlimit --hashlimit-name lobbyctl --hashlimit-mode srcip \
    --hashlimit-above 20/sec --hashlimit-burst 60 -j DROP
iptables -A INPUT -p udp --dport 27911:27926 -m hashlimit --hashlimit-name lobbyrelay --hashlimit-mode srcip \
    --hashlimit-above 800/sec --hashlimit-burst 1600 -j DROP
iptables -A INPUT -p udp --dport 27910:27926 -m hashlimit --hashlimit-name lobbyall \
    --hashlimit-above 8000/sec --hashlimit-burst 16000 -j DROP
iptables -A INPUT -p udp --dport 27910:27926 -j ACCEPT
```

The lobby has limits of its own as well (requests per address, sessions per address, one relay port per address,
log lines per minute), so these rules are a second line, not the only one.

## Use it from the game

On the Multiplayer screen, type the lobby's address (a name or an IP address, with `:port` when it is not 27910)
into "Your own lobby server" on the Host or the Join tab. It is remembered. A game hosted with it shows a code;
other players who typed the same address see the game in their Join list, or join by the code. An invitation
copied from the Host tab names the lobby, so a player who pastes it needs to type nothing.

To check a lobby without the screen, from the game's debug console (`[debug] console=true` in `settings.ini`):

```
coop host 27950 lobby your.lobby.example My test game      # then: coop net  -> "... lobby code ABC123"
coop join code ABC123 your.lobby.example                    # in a second game
```

The lobby's log shows `session ABC123 opened by <address>` and `join ABC123 by <address>`.

## What it is hardened against, and what it shows

Checked on 2026-11-21 by a review with fuzzing (devdocs/plans/MULTIPLAYER_OPEN_ITEMS.md, CO-187):

- A sender must first prove its address (a cookie round trip) before the lobby keeps, lists or introduces anything
  for it, so forged sender addresses get nothing.
- A relay port forwards only between the two addresses its tokens were sent to.
- A session can be changed or moved only with its key.
- No answer is larger than the request it answers.

What a lobby cannot hide: anyone can ask it for the list of games (name, world, rules, number of players, code),
and a join request for a code is answered with the host's address. A game's password is checked by the host's
game, not by the lobby.

## When something does not work

- **A game hosts but gets no code:** the lobby is not reachable on UDP 27910 (both firewalls), or the game and the
  lobby are of different versions of the lobby code.
- **The code works but joining fails:** the relay ports are not open, or `--relay-ports 0`.
- **Two games behind one router and a third outside:** only one game per address can hold a relay port at a time.
- **A name instead of an IP address:** the game looks the name up; the lobby itself never needs DNS.
