#!/usr/bin/env python3
"""FreHair doubleSided off in a GLB (tools/build_actor_lods.py merges the shadow mesh only over one face culling; Fre's own build ran
the LODs before double_hair_fre.py). build_mp.sh turns it back on with ../mm9_fre_claude/scripts/double_hair_fre.py. Args: <in> <out>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if m.get('name', '').startswith('FreHair') and m.pop('doubleSided', False): n += 1
RV.write_glb(sys.argv[2], doc, blob); print('SINGLE hair materials', n)
