"""Fre pass 4: mark the transplanted hair's material (FreHair) doubleSided in a GLB, as PeasantF2 does for its head set: the engine draws
back faces with a flipped normal, so the one-sided hair shell's inside shows hair, not background, wherever it is seen under the rim.
The face material stays single-sided. No geometry change. Args: <in glb> <out glb>"""
import sys
sys.path.insert(0, '../claude_shared')
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if m.get('name', '').startswith('FreHair'): m['doubleSided'] = True; n += 1
RV.write_glb(sys.argv[2], doc, blob)
print('DOUBLE hair materials', n)
