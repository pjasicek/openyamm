#!/bin/bash
# Copies what a game run needs to the second PC (ssh alias oyamm-nb2, see README.md): the built game, the
# development assets, the settings and the launcher. Run it after every build that is to be tested on two machines:
# both games must be the same build with the same content, or the host refuses the join.
#   tools/coop_two_machines/sync.sh
set -euo pipefail
PEER="${OPENYAMM_PEER:-oyamm-nb2}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
ssh "$PEER" 'mkdir -p ~/github/OpenYAMM/build/game ~/github/OpenYAMM/build/tools ~/github/OpenYAMM/build/runtime ~/github/OpenYAMM/tools ~/github/OpenYAMM/output/coop_two_machines'
rsync -a build/game/openyamm "$PEER":github/OpenYAMM/build/game/openyamm
[ -x build/tools/openyamm_lobby_server ] && rsync -a build/tools/openyamm_lobby_server "$PEER":github/OpenYAMM/build/tools/
# The compiled shaders, which the game reads from the checkout's own path: the copy lies at the same path there.
rsync -a --delete build/runtime/ "$PEER":github/OpenYAMM/build/runtime/
rsync -a tools/run_game.sh tools/run_game.py "$PEER":github/OpenYAMM/tools/
rsync -a settings.ini "$PEER":github/OpenYAMM/settings.ini
rsync -a --delete --info=stats1 assets_dev/ "$PEER":github/OpenYAMM/assets_dev/ | tail -3
echo "synced to $PEER: $(ssh "$PEER" 'cd ~/github/OpenYAMM && sha256sum build/game/openyamm | cut -c1-16')"
echo "this PC:        $(sha256sum build/game/openyamm | cut -c1-16)"
