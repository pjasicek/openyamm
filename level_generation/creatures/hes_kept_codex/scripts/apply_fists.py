"""Apply mesh-fitted fists to the unarmed attack before its transition/timing pass."""
import bpy,sys,os,json
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig']
a=bpy.data.actions['Kept_Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for sd in 'LR':
 pose=json.loads((P/'work'/kind/f'fist_{sd}.json').read_text())['finger_local']
 for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f)
  for n,q in pose.items():
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(q);pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
