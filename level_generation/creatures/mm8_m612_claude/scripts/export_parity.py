import bpy,json,re
import numpy as np
from mathutils import Matrix,Vector,kdtree
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final.blend'))
sc=bpy.context.scene;source=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
source_actions={a.name:a for a in bpy.data.actions if a.use_fake_user}
def evaluated(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 co=np.array([tuple(ob.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return co
def action(rig,a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
action(source,None)
for pb in source.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();rest=evaluated(body)
before_o=set(bpy.data.objects);before_a=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/gog_clay.glb'))
new=set(bpy.data.objects)-before_o
rig=next(o for o in new if o.type=='ARMATURE')
mesh=next(o for o in new if o.type=='MESH')
actions={re.sub(r'\.\d+$','',a.name).split('|')[-1]:a for a in set(bpy.data.actions)-before_a}
action(rig,None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();imported=evaluated(mesh)
tree=kdtree.KDTree(len(rest))
for i,p in enumerate(rest):tree.insert(Vector(p),i)
tree.balance();matches=[tree.find(Vector(p)) for p in imported]
print('REST_PARITY',max(x[2] for x in matches),'original',rest.min(0),rest.max(0),'imported',imported.min(0),imported.max(0),'mesh_world',mesh.matrix_world,flush=True)
assert max(x[2] for x in matches)<1e-5
indices=np.array([x[1] for x in matches])
report={}
for name,a in source_actions.items():
 assert name in actions,(name,list(actions))
 action(source,a);action(rig,actions[name])
 maxerr=0;worst=None;standing=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  co=evaluated(body);actual=evaluated(mesh)
  error=np.linalg.norm(co[indices]-actual,axis=1)
  if error.max()>maxerr:maxerr=float(error.max());worst=float(f)
  if name=='Standing':standing.append(float(co[:,2].max()-co[:,2].min()))
 report[name]={'max_position_error_m':maxerr,'frame':worst}
 if standing:report[name]['height_m']=[min(standing),max(standing)]
 print('PARITY',name,report[name],flush=True)
(P/'work/export_parity.json').write_text(json.dumps(report,indent=2))
assert max(v['max_position_error_m'] for v in report.values())<.015
