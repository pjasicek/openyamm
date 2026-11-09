"""Four waist-mounted cloth controls follow the leading thigh, keeping a free front/back hem."""
from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Matrix,Quaternion
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones
for name in ('Front','Back','Left','Right'):
 b=eb.get('B_Wrap_'+name) or eb.new('B_Wrap_'+name)
 b.head=eb['B_'+('L' if name=='Left' else 'R')+'_Thigh'].head if name in ('Left','Right') else Vector((0,.027,1.18))
 b.tail=b.head+Vector((0,0,-.43));b.parent=eb['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
groups={n:(body.vertex_groups.get('B_Wrap_'+n) or body.vertex_groups.new(name='B_Wrap_'+n)) for n in ('Front','Back','Left','Right')}
already=bool(body.get('m488_wrap_margin_applied',False))
if not already and 'orig_co' in me.attributes:
 already=any((v.co-me.attributes['orig_co'].data[v.index].vector).length>.005 for v in me.vertices if me.attributes['piece'].data[v.index].value==1)
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value!=1:continue
 tmargin=float(np.clip((1.10-v.co.z)/.37,0,1));tmargin=tmargin*tmargin*(3-2*tmargin)
 radial=Vector((v.co.x,v.co.y-.027,0));v.co+=radial.normalized()*(0 if already else .025*tmargin)
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 t=float(np.clip((1.18-v.co.z)/.18,0,1));t=t*t*(3-2*t)
 # Account for the different widths of the cloth ellipse.
 side=float(np.clip(abs(v.co.x)/.18,0,1));side=side*side*(3-2*side)
 for name,w in [('Front' if v.co.y<.027 else 'Back',(1-side)*t),('Left' if v.co.x>0 else 'Right',side*t)]:
  if w>1e-7:groups[name].add([v.index],w,'REPLACE')
 if t<1:body.vertex_groups['B_Pelvis'].add([v.index],1-t,'REPLACE')
body['m488_wrap_margin_applied']=True
restpel=rig.data.bones['B_Pelvis'].matrix_local.to_3x3()
rays={s:restpel.inverted()@(rig.data.bones['B_'+s+'_Calf'].head_local-rig.data.bones['B_'+s+'_Thigh'].head_local) for s in 'LR'}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 prev={}
 for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f);pel=rig.pose.bones['B_Pelvis'].matrix.to_3x3().normalized()
  dirs={s:pel.inverted()@(rig.pose.bones['B_'+s+'_Calf'].head-rig.pose.bones['B_'+s+'_Thigh'].head) for s in 'LR'}
  # Use the model's world coordinates inside the pelvis frame, rather than source bone-local axes.
  local={s:restpel@dirs[s] for s in 'LR'};original={s:restpel@rays[s] for s in 'LR'}
  angles={s:math.atan2(-local[s].y,-local[s].z)-math.atan2(-original[s].y,-original[s].z) for s in 'LR'}
  for name in groups:
   b=rig.data.bones['B_Wrap_'+name];pb=rig.pose.bones[b.name]
   if name in ('Front','Back'):
    al,ar=angles.values();mid=(al+ar)/2;spread=math.sqrt((al-ar)**2+.035**2)/2
    angle=mid+(spread if name=='Front' else -spread)
    angle+=math.radians(4 if name=='Front' else -4)
    D=Matrix.Rotation(-angle,3,'X')
   else:
    s='L' if name=='Left' else 'R';D=original[s].rotation_difference(local[s]).to_matrix()
   R=b.matrix_local.to_3x3();q=(R.inverted()@D@R).to_quaternion()
   offset=Vector((0,0,0))
   if name in ('Left','Right'):
    ankle=restpel@(pel.inverted()@(rig.pose.bones['B_'+s+'_Foot'].head-rig.pose.bones['B_'+s+'_Thigh'].head))
    kick=float(np.clip((ankle.z+.65)/.35,0,1));kick=kick*kick*(3-2*kick)
    offset.x=(1 if s=='L' else -1)*0*kick;offset.y=0*kick
   if name=='Back':
    kicks=[]
    for sd in 'LR':
     ankle=restpel@(pel.inverted()@(rig.pose.bones['B_'+sd+'_Foot'].head-rig.pose.bones['B_'+sd+'_Thigh'].head))
     k=float(np.clip((ankle.z+.65)/.35,0,1));kicks.append(k*k*(3-2*k))
    offset.y=0*max(kicks)
   pb.location=R.inverted()@offset;pb.keyframe_insert('location',frame=f)
   if name in prev and q.dot(prev[name])<0:q=-q
   prev[name]=q;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
