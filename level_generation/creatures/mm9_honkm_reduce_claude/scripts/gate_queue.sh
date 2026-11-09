#!/usr/bin/env bash
# Gates before and on a candidate, then LOD checks of both, one after another (one Blender at a time for this agent).
# Usage: gate_queue.sh <candidate glb> <tag>
cd "$(dirname "$0")/.."
scripts/gates.sh before/mm9_honkm.glb before
scripts/gates.sh $1 $2
scripts/blender_queue.sh 0 "installed:before/mm9_honkm.glb:lod" "$2:$1:lod"
echo QUEUEDONE > work/queue_$2.done
