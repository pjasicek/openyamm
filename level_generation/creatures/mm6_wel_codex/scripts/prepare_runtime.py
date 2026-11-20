import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from prepare_actor_glb import prepare
sys.path.insert(0,str(P.parent/'claude_shared'));from region_variants import read_glb,write_glb
prepare(P/'export/mm6_wel_lod0.glb',P/'export/mm6_wel_runtime_lod0.glb')
doc,binary=read_glb(P/'export/mm6_wel_runtime_lod0.glb')
for m in doc['materials']:
 if m['name']=='Foam':m['alphaMode']='MASK';m['alphaCutoff']=.20;m['doubleSided']=True
assert len(doc.get('animations',[]))==9
assert sum(n.get('name')=='Trident' for n in doc['nodes'])==1
write_glb(P/'export/mm6_wel_runtime_lod0.glb',doc,binary)
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')
