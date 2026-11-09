"""Source-frame B_* winged rig; preserve each native animation's actual skin deformation."""
import bpy, json, math, os, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_bind.blend'))
scene=bpy.context.scene
old=bpy.data.objects['Rig']; old.name='SourceRig'; body=bpy.data.objects['Body']
SRC=json.loads((P/'source/humanoid_source_rest.json').read_text())
MAP={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for sd,side in [('L','Left'),('R','Right')]:
 for a,b in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]: MAP[f'B_{sd}_{a}']=side+b
MAP={n:'mixamorig:'+v for n,v in MAP.items()}
for b in old.data.bones:
 if b.name not in MAP.values(): MAP['B_'+b.name]=b.name
INV={v:n for n,v in MAP.items()}
heads={n:old.data.bones[d].head_local.copy() for n,d in MAP.items()}
parents={n:INV.get(old.data.bones[d].parent.name) if old.data.bones[d].parent else None for n,d in MAP.items()}
restold={n:old.data.bones[d].matrix_local.copy() for n,d in MAP.items()}
order=[]
def visit(n):
 order.append(n)
 for c in MAP:
  if parents[c]==n: visit(c)
for n in MAP:
 if parents[n] is None: visit(n)
assert len(order)==len(MAP)==34
rot={};swing={}
for n in order:
 if n not in SRC:
  rot[n]=restold[n].to_3x3();continue
 s=SRC[n];child=s['child']
 if n=='B_Pelvis':q=Quaternion()
 elif child in heads:q=Vector(s['seg']).rotation_difference(heads[child]-heads[n])
 else:q=swing.get(parents[n],Quaternion()).copy()
 swing[n]=q;rot[n]=q.to_matrix()@Matrix(s['rot'])
# Source hands are claws with no finger bones. Use the measured palm's long and transverse axes for their frame.
for sd,side in [('L','Left'),('R','Right')]:
 n=f'B_{sd}_Hand';wr=heads[n];sg=1 if sd=='L' else -1
 f=Vector((sg*.05,-.055,-.08)).normalized();t=Vector((0,-1,0));t=(t-f*t.dot(f)).normalized()
 fs=(Vector(SRC[f'B_{sd}_Finger2']['head'])-Vector(SRC[n]['head'])).normalized()
 ts=Vector(SRC[f'B_{sd}_Finger1']['head'])-Vector(SRC[f'B_{sd}_Finger4']['head']);ts=(ts-fs*ts.dot(fs)).normalized()
 basis=lambda a,b:Matrix((a,b,a.cross(b))).transposed()
 q=(basis(f,t)@basis(fs,ts).transposed()).to_quaternion();swing[n]=q;rot[n]=q.to_matrix()@Matrix(SRC[n]['rot'])
ad=bpy.data.armatures.new('WingedRig');rig=bpy.data.objects.new('Rig',ad);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n in order:
 b=ad.edit_bones.new(n);b.head=heads[n];child=next((c for c in order if parents[c]==n),None)
 length=(heads[child]-heads[n]).length if child else .04
 b.tail=b.head+rot[n].col[1]*max(.01,length);b.align_roll(rot[n].col[2])
 if parents[n]:b.parent=ad.edit_bones[parents[n]]
bpy.ops.object.mode_set(mode='OBJECT')
newrest={n:ad.bones[n].matrix_local.copy() for n in order}
for g in body.vertex_groups:
 if g.name in INV:g.name=INV[g.name]
body.parent=rig
for md in body.modifiers:
 if md.type=='ARMATURE':md.object=rig
old.animation_data_create();rig.animation_data_create()
for tr in old.animation_data.nla_tracks:tr.mute=True
native=list(bpy.data.actions)
results={}
for action in native:
 name=action.name
 old.animation_data.action=action
 if action.slots:old.animation_data.action_slot=action.slots[0]
 start,end=map(float,action.frame_range);duration=(end-start)/24
 samples=sorted(set([k/48 for k in range(math.floor(duration*48)+1)]+[duration]))
 poses=[]
 for t in samples:
  frame=start+t*24;scene.frame_set(math.floor(frame),subframe=frame%1)
  poses.append({n:old.pose.bones[MAP[n]].matrix.copy() for n in order})
 out=bpy.data.actions.new('Winged_'+name);out.use_fake_user=True;rig.animation_data.action=out
 prev={};worst=0
 for t,source in zip(samples,poses):
  target={n:source[n]@restold[n].inverted()@newrest[n] for n in order}
  for n in order:
   parent=parents[n]
   basis=(newrest[n].inverted()@newrest[parent]@target[parent].inverted()@target[n]) if parent else newrest[n].inverted()@target[n]
   loc,q,scale=basis.decompose()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
   for path in ('location','rotation_quaternion','scale'):pb.keyframe_insert(path,frame=t*48)
   err=np.max(np.abs(np.array(target[n]@newrest[n].inverted())-np.array(source[n]@restold[n].inverted())))
   worst=max(worst,float(err))
  bpy.context.view_layer.update()
  actual=max(float(np.max(np.abs(np.array(rig.pose.bones[n].matrix@newrest[n].inverted())-np.array(source[n]@restold[n].inverted())))) for n in order)
  worst=max(worst,actual)
 out.use_frame_range=True;out.frame_start=0;out.frame_end=duration*48
 for layer in out.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 assert worst<2e-5,(name,worst)
 results[out.name]={'duration_s':duration,'samples':len(samples),'max_deformation_matrix_error':worst}
 print('CLIP',out.name,results[out.name],flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for a in native:bpy.data.actions.remove(a)
bpy.data.objects.remove(old,do_unlink=True)
scene.render.fps=48
scene['rig_offsets']=json.dumps({n:{'q':list(swing[n]),'R_src':SRC[n]['rot']} for n in swing})
scene['source_map']=json.dumps(MAP)
bpy.context.view_layer.update()
(P/'work/base_rig_check.json').write_text(json.dumps(results,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/winged_base_rig.blend'))
print('BASE_RIG_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
