import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from prepare_actor_glb import prepare
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
prepare(P/'export/lods.glb',P/'export/prepared.glb')
from build_actor_lods import read_glb,write_glb
d,b=read_glb(P/'export/prepared.glb')
for m in d['materials']:m.pop('occlusionTexture',None)
write_glb(P/'export/prepared.glb',d,b)
R.apply_variants(P/'export/prepared.glb',P/'export/mm8_m464.glb',P/'textures/m464_ramps.json',[(prefix,key,value) for prefix in ['VampirePeasant_','VampirePeasantHead_'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
sys.argv=['merge_head_material.py',str(P/'export/mm8_m464.glb'),str(P/'export/mm8_m464.glb')];runpy.run_path('tools/merge_head_material.py',run_name='__main__')
