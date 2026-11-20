"""Join the six rigid primitives into the runtime LOD source, then build the shared colour/shadow chains."""
import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate,read_glb,write_glb
source=P/'export/mm8_m624_runtime_lod0.glb';doc,blob=read_glb(source);node=next(n for n in doc['nodes']if n.get('name')=='Body');mesh=doc['meshes'][node['mesh']]
for sd in ['L1','L2','L3','R1','R2','R3']:
 prop=next(n for n in doc['nodes']if n.get('name')==sd+'_Weapon');assert prop['skin']==node['skin']
 for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]),('matrix',None)]:assert prop.get(key,default)==node.get(key,default),(sd,key)
 mesh['primitives'].extend(doc['meshes'][prop.pop('mesh')]['primitives']);prop.pop('skin')
doc['meshes']=[mesh];node['mesh']=0;joined=P/'export/mm8_m624_joined.glb';write_glb(joined,doc,blob)
generate(joined.resolve(),(P/'export/mm8_m624_lods.glb').resolve(),'Body',ratios=(.5,.25,.125),max_influences=4)
