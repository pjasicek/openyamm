#!/bin/bash
# Lists what in the scratch root is stale against assets_dev: the Xeen world's common event scripts (A3 rewrites them
# by rename, leaving a stale hard link here) and the world's data tables (a real copy). Prints the commands to run
# (each rm with a literal path, as the repository's rule asks); run them by hand.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR; A=assets_dev/worlds/xeen; T=output/studio_cal/dd22/root/worlds/xeen
cd $R
for f in $A/events/common/*; do
  b=$(basename $f)
  [ "$(stat -c %i $f)" != "$(stat -c %i $T/events/common/$b 2>/dev/null)" ] && echo "rm $T/events/common/$b; ln $f $T/events/common/$b"
done
diff -rq $A/data_tables $T/data_tables >/dev/null || echo "rm -r $T/data_tables; cp -r $A/data_tables $T/data_tables"
true
