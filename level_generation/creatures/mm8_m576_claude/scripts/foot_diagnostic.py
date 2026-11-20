"""Use the exported sole selectors for the running heading and preserve any remaining LOD grip samples."""
import bpy,runpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');a=g['Glb'](P/'export/mm8_m576.glb');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg);m=g['load_meshes'](a)[0];g['configure_mesh'](m,cfg,r)
checkpoint=P/'work/master_before_sole_heading.blend'
if not checkpoint.exists():
 import shutil;shutil.copyfile(P/'work/master_textured_uv.blend1',checkpoint)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sys.path.insert(0,str(P/'scripts'));import armik
tree=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(body.matrix_world@v.co,v.index)
tree.balance();soles={}
for side,(ids,heel,toe) in m.feet.items():
 soles[side]=tuple(np.array([tree.find(Vector(m.rest[i]))[1] for i in subset]) for subset in (ids,heel,toe))
def verts():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(body.matrix_world@x.co) for x in me.vertices]);ev.to_mesh_clear();return v

for side,(ids,heel,toe) in soles.items():
 print('SOLE',side,'count',len(ids),'heel',heel.tolist(),'toe',toe.tolist())
 for i in np.unique(np.r_[heel,toe]):
  v=body.data.vertices[i];print(i,list(v.co),[(body.vertex_groups[e.group].name,round(e.weight,3)) for e in v.groups])
