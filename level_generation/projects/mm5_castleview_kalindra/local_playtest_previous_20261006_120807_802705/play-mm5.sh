#!/bin/sh
set -eu
cd /home/pjasicek/github/OpenYAMM/level_generation/projects/mm5_castleview_kalindra/local_playtest/playtest
exec /home/pjasicek/github/OpenYAMM/level_generation/projects/mm5_castleview_kalindra/local_playtest/bin/openyamm --world mm5 "$@"
