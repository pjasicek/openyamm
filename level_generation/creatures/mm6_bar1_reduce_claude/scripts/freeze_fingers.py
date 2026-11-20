#!/usr/bin/env python3
"""Hold the left fingers at their rest curl in every clip: remove the animation channels (and their samplers) that
target B_L_Finger* nodes, so those joints keep their node rotation. The Meshy left hand fuses the thumb tip to the
ring and middle fingers in the curled rest pose; finger motion stretched those faces into spikes (up to 11 cm in Hit).
The accessors of removed samplers stay unreferenced (a few KB). Usage: freeze_fingers.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src)
frozen = {i for i, n in enumerate(doc['nodes']) if n.get('name', '').startswith('B_L_Finger')}
removed = 0
for a in doc['animations']:
    keep = [c for c in a['channels'] if c['target'].get('node') not in frozen]
    removed += len(a['channels']) - len(keep)
    used = sorted({c['sampler'] for c in keep}); remap = {old: new for new, old in enumerate(used)}
    a['samplers'] = [a['samplers'][i] for i in used]
    for c in keep: c['sampler'] = remap[c['sampler']]
    a['channels'] = keep
R.write_glb(dst, doc, binary); print('FROZE', len(frozen), 'nodes;', removed, 'channels removed ->', dst)
