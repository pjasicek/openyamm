#!/bin/bash
# fist -> crown -> mantle spikes -> nape weights -> throat tunnel: work/parts_r4.blend (project folder). The mesh blend rebuild.sh exports.
R=$PWD
F='^(GRIP|THUMB|STAFF|FISTDONE|Trace)' W=300 scripts/run.sh fist_yan.py $R/work/uv_v1.blend $R/work/fist_v3.blend $R/work/hand_poses.json
F='^(CROWN|Trace)' scripts/run.sh attach_crown.py $R/work/fist_v3.blend $R/work/parts_r4a.blend
F='^(SPIKES|Trace)' scripts/run.sh spikes.py $R/work/parts_r4a.blend $R/work/parts_r4b.blend 0.6
F='^(NAPE|Trace)' scripts/run.sh nape_relax.py $R/work/parts_r4b.blend $R/work/parts_r4c.blend 24
F='^(TUNNEL|Trace)' scripts/run.sh tunnel_close.py $R/work/parts_r4c.blend $R/work/parts_r4.blend
F='^(HAIR|Trace)' scripts/run.sh hair_widen.py $R/work/parts_r4.blend $R/work/parts_r5.blend 0.30
