"""Release the maul onto its broad side beside the corpse, with the same world anchor in Dead."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
r=bpy.data.objects['Rig'];r.animation_data_create();sc=bpy.context.scene;weapon='Thunder_Maul';obj=bpy.data.objects[weapon]
local=[r.data.bones[weapon].matrix_local.inverted()@v.co for v in obj.data.vertices]
def low(m):return min((m@p).z for p in local)
for a in [a for a in bpy.data.actions if a.name.startswith('Forge_') and a.name not in ('Forge_Death','Forge_Dead')]:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in (int(a.frame_range[0]),int(a.frame_range[1])):
  sc.frame_set(f);b=r.pose.bones[weapon];b.matrix_basis.identity();b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
r.pose.bones[weapon].matrix_basis.identity()
a=bpy.data.actions['Forge_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);release=armik.W(r,weapon).copy()
y=release.to_3x3().col[1];y.z=0;y.normalize();z=Vector((0,0,-1));x=y.cross(z).normalized();anchor=Matrix((x,y,z)).transposed().to_4x4();anchor.translation=release.translation+Vector((-1.15,-.75,0));anchor.translation.z+=.002-low(anchor)
for clip in ('Forge_Death','Forge_Dead'):
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[]
 for tick in range(int(a.frame_range[1]*4)+1):
  f=tick/4;sc.frame_set(int(f),subframe=f-int(f));k=min(1,f/15) if clip.endswith('Death') else 1;k=k*k*(3-2*k)
  m=release.to_quaternion().slerp(anchor.to_quaternion(),k).to_matrix().to_4x4();m.translation=release.translation.lerp(anchor.translation,k);m.translation.z+=max(0,.002-low(m))
  armik.set_world(r,weapon,m);assert (armik.W(r,weapon).translation-m.translation).length<1e-5
  keys.append((f,r.pose.bones[weapon].matrix_basis.copy()))
 prev=None
 for f,m in keys:
  b=r.pose.bones[weapon];q=m.to_quaternion()
  if prev is not None and q.dot(prev)<0:q=-q
  prev=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 print('MAUL_DROP',clip,len(keys),'keys, support height',low(anchor),flush=True)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=out)
