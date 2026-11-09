"""Physical support uses the shoe and peg surfaces; audit the real staff against the body."""
import bpy,sys,json,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_uv.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['StaffMesh'];sc=bpy.context.scene
def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
# Dense contact keys must use the same linear interpolation as the delivered glTF.
for action in bpy.data.actions:
 for curve in fcurves(action):
  for key in curve.keyframe_points:key.interpolation='LINEAR'

parts=np.array([a.value for a in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices]);feet=np.isin(parts,[6,12]) & (rest[:,2]<.10)
assert feet.sum()>30
for v in body.data.vertices:
 weights=sorted([(e.group,e.weight) for e in v.groups],key=lambda x:-x[1]);keep=weights[:4];total=sum(w for _,w in keep);assert total>0
 for g,w in weights:body.vertex_groups[g].remove([v.index])
 for g,w in keep:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
def coords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([(obj.matrix_world@v.co)[:] for v in m.vertices]);ev.to_mesh_clear();return co
def select(a):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();report={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];select(a);rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));b=coords(body);s=coords(staff)
  low=min(b[:,2].min(),s[:,2].min()) if name=='Death' else b[feet,2].min()
  dz=max(0,.002-low) if name=='Running' else .002-low
  rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,float(dz))),float(dz)))
 for f,loc,dz in rows:
  rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
 report[name]={'root_correction_cm':[min(r[2] for r in rows)*100,max(r[2] for r in rows)*100]}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Retain separate Cast and Dead roles for portable review/export.
for n in ['Cast','Dead']:
 if n in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[n])
a=bpy.data.actions['Attack'].copy();a.name='Cast';a.use_fake_user=True
select(bpy.data.actions['Death']);sc.frame_set(39);pose={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
a=bpy.data.actions.new('Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in [0,3]:
 for n,(q,l) in pose.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=3
# Exact staff/body face intersections, excluding the gripping hand and its cuff.
faces=[list(f.vertices) for f in body.data.polygons if int(parts[f.vertices[0]]) not in [5,11,14]]
faceparts=[int(parts[f.vertices[0]]) for f in body.data.polygons if int(parts[f.vertices[0]]) not in [5,11,14]]
sfaces=[list(f.vertices) for f in staff.data.polygons]
jaw=rig.data.bones['B_Head'].head_local.z-.02
headfaces=[list(f.vertices) for f in body.data.polygons if all(parts[i]==1 and rest[i,2]>jaw for i in f.vertices)]
shoulderfaces=[list(f.vertices) for f in body.data.polygons if all(parts[i]==0 and abs(rest[i,0])>.12 and rest[i,2]>1.2 for i in f.vertices)]
for name in report:
 select(bpy.data.actions[name]);low=10;bodylow=10;hits={};headhits={}
 for f in np.arange(0,float(rig.animation_data.action.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));b=coords(body);s=coords(staff);low=min(low,float(s[:,2].min()));bodylow=min(bodylow,float(b[:,2].min()))
  hpairs=BVHTree.FromPolygons(b.tolist(),headfaces).overlap(BVHTree.FromPolygons(b.tolist(),shoulderfaces))
  if hpairs:headhits[str(f)]=len(hpairs)
  pairs=BVHTree.FromPolygons(b.tolist(),faces).overlap(BVHTree.FromPolygons(s.tolist(),sfaces))
  if pairs:hits[str(f)]=dict((str(k),sum(faceparts[i]==k for i,j in pairs)) for k in set(faceparts[i] for i,j in pairs))
 report[name].update(staff_lowest_m=low,staff_body_intersections=hits,head_shoulder_intersections=headhits,body_lowest_m=bodylow)
 print('PHYSICAL',name,'root cm',report[name]['root_correction_cm'],'staff floor',round(low,4),'intersection frames',len(hits),'pieces',sorted(set(k for row in hits.values() for k in row)))
(P/'review/final_physics.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_settled.blend'))

assert not any(v['staff_body_intersections'] for v in report.values()), 'Staff/body contact remains'
assert min(v['staff_lowest_m'] for v in report.values())>=.001

assert not any(v['head_shoulder_intersections'] for v in report.values()), 'Head/shoulder contact remains'
assert min(v['body_lowest_m'] for v in report.values())>=.001
