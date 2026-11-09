"""The head-set materials single-sided again for tools/build_actor_lods.py (its merged shadow mesh needs one face culling;
the creature's build made the LODs before double_head.py). build_mp.sh runs ../mm9_peasantf2_claude/scripts/double_head.py
after the LODs, as build_runtime.sh does. Args: <in glb> <out glb>"""
import sys
sys.path.insert(0, '../claude_shared')
import region_variants as RV
doc, blob = RV.read_glb(sys.argv[1]); n = 0
for m in doc['materials']:
    if 'Head' in m.get('name', '') and m.get('doubleSided'):
        m.pop('doubleSided'); n += 1
RV.write_glb(sys.argv[2], doc, blob)
print('SINGLE head materials', n)
