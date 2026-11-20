#!/bin/bash
# Wait until no game runs (one game process machine-wide), then run the private-user-data tour (minimized, exits by
# itself). Usage: scripts/run_ingame.sh <log name>
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_dragonking_claude; U=$PWD/$P/work/ingame_userdata
while true; do
  while pgrep -x openyamm >/dev/null; do sleep 4; done
  sleep 1
  pgrep -x openyamm >/dev/null || break
done
cp $P/work/ingame_settings_template.ini $U/settings.ini   # the game rewrites settings.ini on exit
timeout 300 ./tools/run_game.sh --user-data $U > $P/work/$1.log 2>&1
echo "exit $?"
grep "Menu tour console: map\|Monsters spawned\|rror" $U/openyamm.log | tail -20
