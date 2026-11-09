#!/bin/bash
P=level_generation/creatures/mm9_monk_claude
$P/scripts/codex_paint.sh & 
for t in a b c; do $P/scripts/codex_heads.sh $t & done
wait; echo paint-all-done
