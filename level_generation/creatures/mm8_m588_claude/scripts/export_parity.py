"""Reimport the actual portable GLB and compare every clip at half-frame intervals."""
import bpy,json,re
import numpy as np
from mathutils import Matrix,Vector,kdtree
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/boulder_master.blend'))
sc=bpy.context.scene;source=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
source_actions={a.name:a for a in bpy.data.actions if a.use_fake_user}
def evaluated(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(ob.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return co
def action(rig,a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
action(source,None)
for pb in source.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();rest=evaluated(body)
before_o=set(bpy.data.objects);before_a=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(P/'export/boulder_portable.glb'))
new=set(bpy.data.objects)-before_o;rig=next(o for o in new if o.type=='ARMATURE');mesh=next(o for o in new if o.type=='MESH')
actions={re.sub(r'\.\d+$','',a.name).split('|')[-1]:a for a in set(bpy.data.actions)-before_a}
action(rig,None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();imported=evaluated(mesh)
tree=kdtree.KDTree(len(rest))
for i,p in enumerate(rest):tree.insert(Vector(p),i)
tree.balance();matches=[tree.find(Vector(p)) for p in imported]
assert max(x[2] for x in matches)<1e-5
indices=np.array([x[1] for x in matches]);report={}
for name,a in source_actions.items():
 assert name in actions
 action(source,a);action(rig,actions[name]);errors=[];ground=[];endpoints=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)));co=evaluated(body);actual=evaluated(mesh)
  errors.append(float(np.linalg.norm(co[indices]-actual,axis=1).max()));ground.append(float(actual[:,2].min()))
  if f in (0,a.frame_range[1]):endpoints.append(actual)
 report[name]={'max_position_error_m':max(errors),'min_ground_m':min(ground),'max_ground_m':max(ground)}
 if name in ('Standing','Walking','Dead'):
  report[name]['loop_seam_m']=float(np.linalg.norm(endpoints[0]-endpoints[-1],axis=1).max());assert report[name]['loop_seam_m']<1e-5
 assert max(errors)<.001,(name,max(errors))
 assert min(ground)>-.001,(name,min(ground))
 print(name,report[name],flush=True)
(P/'work/export_parity.json').write_text(json.dumps(report,indent=2)+'\n')
