"""Mark the head-set materials (name contains 'Head': the head, hair and braid paint, every tier variant) doubleSided in a GLB: the engine then
draws their back faces with a flipped normal (fs_model.sc), so the one-sided hair shell's inside shows hair instead of background under the
rim (see-through gate). No geometry change. Args: <in glb> <out glb>"""
import sys
sys.path.insert(0, '../claude_shared')
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if 'Head' in m.get('name', ''): m['doubleSided'] = True; n += 1
RV.write_glb(sys.argv[2], doc, blob)
print('DOUBLE head materials', n)
