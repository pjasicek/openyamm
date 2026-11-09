"""Mark the body material (cloth: robe, tabard, hood, sleeves; name 'Skraelos', not the head set) doubleSided in a GLB: the engine then draws
its back faces with a flipped normal (fs_model.sc), so the inside of the hood, the sleeves and the robe (seen under the hem and in the fall)
shows cloth instead of the background (see-through gate), as PeasantF7's head set. Replaces the lining twins. Args: <in glb> <out glb>"""
import sys
sys.path.insert(0, '../claude_shared')
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if m.get('name', '').startswith('Skraelos') and 'Head' not in m.get('name', ''): m['doubleSided'] = True; n += 1
RV.write_glb(sys.argv[2], doc, blob)
print('DOUBLE body materials', n)
