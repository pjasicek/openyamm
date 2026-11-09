"""Clear doubleSided on the body material ('Skraelos') for the LOD build: tools/build_actor_lods.py merges the shadow geometry only over
materials with the same face culling; ../mm9_skraelos_claude/scripts/double_body.py sets it again after the LODs, the order of the
creature's build_runtime_sk.sh. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if m.get('name') == 'Skraelos' and m.get('doubleSided'):
        m['doubleSided'] = False; n += 1
RV.write_glb(sys.argv[2], doc, blob)
print('SINGLE body materials', n)
