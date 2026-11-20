#!/bin/bash
# Three lanes of rebuild_map.sh, then The Thousand Terrors alone (another agent's map; last, as asked).
R=/home/pjasicek/github/OpenYAMM/level_generation/projects/mm9r_common/rebuild_1031
cd /home/pjasicek/github/OpenYAMM
lane() { for item in "$@"; do $R/rebuild_map.sh ${item%:*} $( [ "${item#*:}" = probe ] && echo probe ); echo "$(date +%H:%M:%S) ${item%:*}" >> $R/lanes_done.txt; done; }
lane yanmirsfort:probe klusoshouse verhoffinruins dungeonofsecrets hallofthegods dragonstadium thearena:probe traininghall:probe &
a=$!
lane tasaracademy:probe thjoradmine inventastorca dookscastle bathhouse ruinedtemple:probe connectingtunnels darkpassageway &
b=$!
lane templeofhonk:probe anskramkeep lichlab:probe chasmofthedead:probe beethoven drangheimprison lindisfarnemonastery:probe &
c=$!
wait $a $b $c
$R/rebuild_map.sh 1000terrors probe; echo "$(date +%H:%M:%S) 1000terrors" >> $R/lanes_done.txt
echo ALL_DONE >> $R/lanes_done.txt
