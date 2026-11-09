import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
d,b=read_glb(E/'mm6_wel_runtime_lod0.glb')
body=next(n for n in d['nodes'] if n.get('name')=='Body');prop=next(n for n in d['nodes'] if n.get('name')=='TridentMesh')
assert {k:v for k,v in body.items() if k not in ['mesh','name']}=={k:v for k,v in prop.items() if k not in ['mesh','name']}
item_index=prop.pop('mesh');d['meshes'][body['mesh']]['primitives']+=d['meshes'][item_index]['primitives'];prop.pop('skin')
d['meshes'].pop(item_index)
for n in d['nodes']:
 if n.get('mesh',-1)>item_index:n['mesh']-=1
# The LOD builder merges opaque shadow materials; use one consistent culling mode before installation.
for m in d['materials']:m['doubleSided']=True
write_glb(E/'mm6_wel_combined_lod0.glb',d,b)
sys.argv=['build_actor_lods.py',str(E/'mm6_wel_combined_lod0.glb'),str(E/'mm6_wel_lods.glb'),'--mesh-node','Body']
runpy.run_path('tools/build_actor_lods.py',run_name='__main__')
