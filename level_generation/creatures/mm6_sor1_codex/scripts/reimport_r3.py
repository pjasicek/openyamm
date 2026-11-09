"""Verify exported surface parity and restore piece labels solely for the exported-mesh contact audit."""
import bpy,bmesh,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
p=Path(__file__).resolve().parents[1];level=int(sys.argv[sys.argv.index('--')+1])
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'round3_lod{level}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
G=json.loads((p/'work/grip_pose.json').read_text());hm=rig.matrix_world@rig.data.bones['B_R_Hand'].matrix_local
C=hm@Vector(G['handle_centre_hand_local']);axis=hm.to_3x3()@Vector(G['handle_axis_hand_local'])
rest=np.array([tuple(o.matrix_world@x.co) for o in [body,staff] for x in o.data.vertices]);pieces=[a.value for a in body.data.attributes['piece'].data]+[200]*len(staff.data.vertices)
count=len(body.data.vertices);samples={};bounds={}
def set_action(a):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix()
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
def points(objects):
 out=[]
 for o in objects:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out.extend(tuple(o.matrix_world@x.co) for x in me.vertices);ev.to_mesh_clear()
 return np.array(out)
for a in [bpy.data.actions[n] for n in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']]:
 set_action(a);duration=(a.frame_range[1]-a.frame_range[0])/scene.render.fps
 for t in np.linspace(0,duration,5):
  t=round(t*scene.render.fps)/scene.render.fps;f=t*scene.render.fps;scene.frame_set(int(f),subframe=f-int(f));xyz=points([body,staff]);samples[(a.name,float(t))]=xyz
  if t==0:bounds[a.name]={'body_min':xyz[:count].min(0).tolist(),'body_max':xyz[:count].max(0).tolist(),'staff_min':xyz[count:].min(0).tolist(),'staff_max':xyz[count:].max(0).tolist()}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=120
bpy.ops.import_scene.gltf(filepath=str(p/'work'/f'round3_lod{level}_audit.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';body=bpy.data.objects['Sorcerer'];scene=bpy.context.scene
set_action(None) if False else None
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
tree=kdtree.KDTree(len(rest))
for i,x in enumerate(rest):tree.insert(Vector(x),i)
tree.balance();mapping=[];dist=[]
for x in body.data.vertices:
 _,i,d=tree.find(body.matrix_world@x.co);mapping.append(i);dist.append(d)
print('REST_DIAG',body.name,body.matrix_world,'source bbox',rest.min(0),rest.max(0),'import bbox',np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices]).min(0),np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices]).max(0),'dist percentiles',np.percentile(dist,[0,50,90,99,100]),flush=True)
assert max(dist)<.00002,max(dist)
errors={}
for (name,t),expected in samples.items():
 a=bpy.data.actions[name];set_action(a);f=t*scene.render.fps;scene.frame_set(int(f),subframe=f-int(f));xyz=points([body]);error=float(np.linalg.norm(xyz-expected[mapping],axis=1).max()*1000);errors[name]=max(errors.get(name,0),error)
assert max(errors.values())<.2,errors
# Bake the mesh object's transform into its rest vertices; armature modifier preserves world deformation.
body.data.transform(body.matrix_world.copy());body.matrix_world=Matrix()
attr=body.data.attributes.new('piece','INT','POINT')
for i,j in enumerate(mapping):attr.data[i].value=pieces[j]
# Separate the already-authored rigid staff for the same body/prop contact tests.
body.name='Body';staff=body.copy();staff.data=body.data.copy();bpy.context.collection.objects.link(staff);staff.name='Staff'
for o,keep_staff in [(body,False),(staff,True)]:
 bm=bmesh.new();bm.from_mesh(o.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v[layer]==200)!=keep_staff],context='VERTS');bm.to_mesh(o.data);bm.free()
hm=rig.matrix_world@rig.data.bones['B_R_Hand'].matrix_local
G['handle_centre_hand_local']=list(hm.inverted()@C);G['handle_axis_hand_local']=list((hm.to_3x3().inverted()@axis).normalized())
(p/'work/runtime_grip_pose.json').write_text(json.dumps(G,indent=2))
report={'rest_mapping_max_mm':max(dist)*1000,'surface_parity_max_mm':errors,'bounds_at_clip_start':bounds,'import_fps':scene.render.fps,'joints':len(rig.data.bones),'maximum_influences':max(len([g for g in v.groups if g.weight>1e-6]) for v in body.data.vertices)}
assert report['maximum_influences']<=8 and report['joints']<=128,report
(p/'work'/f'export_parity_lod{level}_r3.json').write_text(json.dumps(report,indent=2));print('EXPORT_PARITY',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/f'runtime_lod{level}_r3.blend'))
