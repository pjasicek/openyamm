import bpy,sys,math,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_clips.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
# Ragged shoulder cloth hangs from the collarbone, behind the humerus; arm-parenting swept it into the skull.
for side,pieces in [('L',{16,27}),('R',{17,26})]:
 ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value in pieces]
 for g in body.vertex_groups:g.remove(ids)
 group=body.vertex_groups.get(f'B_{side}_Clavicle') or body.vertex_groups.new(name=f'B_{side}_Clavicle')
 group.add(ids,1.,'REPLACE')
act=bpy.data.actions['Walking'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
# Five degrees of shoulder abduction keeps long skeletal fingers clear of the thighs.
for f in range(int(act.frame_range[1])+1):
 scene.frame_set(f)
 for side,sign in [('L',-1),('R',1)]:
  pb=rig.pose.bones[f'B_{side}_UpperArm'];m=pb.matrix.copy();t=m.translation.copy()
  m=Matrix.Rotation(sign*math.radians(5),4,'Y')@m;m.translation=t
  pb.matrix=m;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Reduce rigid pieces separately after weighting; keep the main skull and small finger segments intact.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
parts=[o for o in bpy.context.selected_objects if o.type=='MESH'];report=[]
for ob in parts:
 bpy.context.view_layer.objects.active=ob
 pid=ob.data.attributes['piece'].data[0].value;n=len(ob.data.polygons)
 ratio=1 if pid==100 or n<90 else (.28 if pid>=100 else .5)
 if ratio<1:
  mod=ob.modifiers.new('Budget','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
  bpy.ops.object.modifier_apply(modifier=mod.name)
 report.append([pid,n,len(ob.data.polygons)])
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Body'
for poly in body.data.polygons:poly.use_smooth=True
print('REDUCTION',sum(r[1] for r in report),sum(r[2] for r in report));json.dump(report,open(P/'work/reduction.json','w'),indent=1)
assert sum(r[2] for r in report)<17000
# Root-only clearance at quarter frames prevents the curved feet from dipping between baked keys.
from mathutils import Vector
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 nf=int(act.frame_range[1]);corr=[0.]*(nf+1);locations=[]
 for f in range(nf+1):
  scene.frame_set(f);locations.append(rig.pose.bones['B_Pelvis'].location.copy())
 for i in range(nf*4+1):
  f=i/4;scene.frame_set(int(f),subframe=f-int(f))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  dz=max(0.,.00025-min((body.matrix_world@v.co).z for v in mesh.vertices));ev.to_mesh_clear()
  for j in {int(f),min(nf,int(math.ceil(f)))}:corr[j]=max(corr[j],dz)
 rig.animation_data.action=None
 for i,l in enumerate(locations):
  pb=rig.pose.bones['B_Pelvis'];pb.location=l+inv@Vector((0,0,corr[i]))
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];pb.keyframe_insert('location',frame=i);rig.animation_data.action=None
 print('SUBFRAME_FLOOR',act.name,max(corr))
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'))
