#!/usr/bin/env python3
"""Like-for-like jitter reference: <glb> with its clips replaced by those of the creature's untouched-clip reference
(../mm9_lizardorc_claude/work/ref_half.glb, same 69 nodes in the same order). jitter_gate.py compares the shoulder-skin
95th percentile of one mesh against another; with the reduced mesh against ref_half's old mesh the vertex population
differs, so the reference is rebuilt on the same mesh. Usage: ref_swap.py <glb> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
ref, rbin = read_glb(Path(__file__).resolve().parents[2] / 'mm9_lizardorc_claude' / 'work' / 'ref_half.glb')
assert [n.get('name') for n in ref['nodes']] == [n.get('name') for n in doc['nodes']]
anims = []
for a in ref['animations']:
    a = copy.deepcopy(a)
    for s in a['samplers']:
        s['input'] = append_accessor(doc, binary, ref['accessors'][s['input']], accessor_bytes(ref, rbin, s['input']))
        s['output'] = append_accessor(doc, binary, ref['accessors'][s['output']], accessor_bytes(ref, rbin, s['output']))
    anims.append(a)
doc['animations'] = anims
write_glb(Path(sys.argv[2]), doc, bytes(binary)); print('REF', sys.argv[2], len(anims), 'clips')
