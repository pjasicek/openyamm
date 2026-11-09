#!/usr/bin/env python3
"""hkr: after the attachments are split out of the colour LODs, rebuild every shadow LOD from its (now bare) colour
LOD with tools/build_actor_lods.py's merge_shadow, so a descriptor that does not list an attachment (tier A and C
have no carapace) casts no shadow of it. Run before shrink_shadow_lods.py. Usage: rebuild_shadows_hkr.py in out"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as bal  # noqa
from merge_head_material import write_glb  # noqa
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from region_variants import _compact as compact  # (Nobles) keeps extras' texture references (burn maps)
document, binary = bal.read_glb(Path(sys.argv[1])); binary = bytearray(binary)
base = next(i for i, m in enumerate(document['meshes']) if 'openyamm_lods' in m.get('extras', {}))
ex = document['meshes'][base]['extras']; chain = [base] + ex['openyamm_lods']
for colour, shadow in zip(chain, ex['openyamm_shadow_lods']):
    document['meshes'][shadow] = bal.merge_shadow(document, binary, document['meshes'][colour])
write_glb(Path(sys.argv[2]), *compact(document, bytes(binary)))
print('SHADOWS rebuilt', len(chain))
