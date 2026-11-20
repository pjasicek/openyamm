"""Physical support uses the shoe and peg surfaces; audit the real staff against the body."""
import bpy,sys,json,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['StaffMesh'];sc=bpy.context.scene
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
for name in report:
 select(bpy.data.actions[name]);low=10;hits={}
 for f in range(int(rig.animation_data.action.frame_range[1])+1):
  sc.frame_set(f);b=coords(body);s=coords(staff);low=min(low,float(s[:,2].min()))
  pairs=BVHTree.FromPolygons(b.tolist(),faces).overlap(BVHTree.FromPolygons(s.tolist(),sfaces))
  if pairs:hits[str(f)]=dict((str(k),sum(faceparts[i]==k for i,j in pairs)) for k in set(faceparts[i] for i,j in pairs))
 report[name].update(staff_lowest_m=low,staff_body_intersections=hits)
 print('PHYSICAL',name,'root cm',report[name]['root_correction_cm'],'staff floor',round(low,4),'intersection frames',len(hits),'pieces',sorted(set(k for row in hits.values() for k in row)))
(P/'work/physical_review.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/grounded.blend'))
common.workbench_clay(sc)
for view in ['front','left','back']:
 rows=[];out=P/'review'/('equipped_'+view);out.mkdir(exist_ok=True)
 for name in report:
  select(bpy.data.actions[name]);row=[];end=float(rig.animation_data.action.frame_range[1])
  for i in range(7):
   f=end*i/6;sc.frame_set(int(f),subframe=f%1)
   target=(0,.35) if name=='Death' else (0,0)
   path=common.render_views(str(out/(name+'_'+str(i))),.75,2.7,views=(view,),resolution=(300,420),target=target)[0];row.append([path,f'{name} {f:.1f}'])
  rows.append(row)
 (out/'frames.json').write_text(json.dumps(rows))
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('g5_hand_stretch.py',P/'work/grounded.blend',*report)
run('g4_weights.py',P/'work/grounded.blend','equipped','Standing:0','Walking:8','Running:11','Attack:37','Fidget:21','Hit:7','Death:18')
