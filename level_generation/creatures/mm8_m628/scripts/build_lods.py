"""Four color/shadow LODs, preserving finger endpoints, soles and bow nocks."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate,read_glb
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m628_master.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];piece=np.array([x.value for x in body.data.attributes['piece'].data]);co=np.array([tuple(v.co)for v in body.data.vertices]);points=[]
fj=json.loads((P/'work/finger_joints.json').read_text())
for side in 'LR':
    ids=np.where((piece==5)if side=='R'else((piece>=3000)&(piece<4000)))[0]
    for chain in fj[side].values():
        i=int(ids[np.argmin(np.linalg.norm(co[ids]-chain[-1],axis=1))]);points.append(tuple(co[i]))
for pid in [1,18,25,28,29,31,34]:
    ids=np.where(piece==pid)[0]
    if len(ids):points.extend(tuple(co[i])for i in ids[np.argsort(co[ids,2])[:2]])
for v in json.loads(bpy.context.scene['bow_local'])['tips']:
    p=rig.data.bones['Bow'].matrix_local@Vector(v);ids=np.where(piece==4000)[0];points.append(tuple(co[ids[np.argmin(np.linalg.norm(co[ids]-np.array(p),axis=1))]]))
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P/'export/mm8_m628_lod0.glb',P/'export/mm8_m628_lods.glb','SkeletonArcher',ratios=(.5,.25,.125),max_influences=4,protected_points=points)
d,_=read_glb(P/'export/mm8_m628_lods.glb');node=next(n for n in d['nodes']if n.get('name')=='SkeletonArcher');base=node['mesh'];indices=[base]+d['meshes'][base]['extras']['openyamm_lods'];counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in indices]
assert all(b<a for a,b in zip(counts,counts[1:])),counts
(P/'export/lods.json').write_text(json.dumps({'triangles':counts,'protected_points':points,'ratios':[.5,.25,.125],'influence_limit':4},indent=2));print('LODS',counts)
