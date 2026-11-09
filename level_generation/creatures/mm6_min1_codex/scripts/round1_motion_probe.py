import bpy,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
for f in [100,105,110,115]:
 bpy.context.scene.frame_set(f);cur={n:r.pose.bones[n].matrix.to_quaternion() for n in r.pose.bones.keys() if 'Arm' in n or 'Hand' in n or 'Forearm' in n}
 print('ROT',f,{n:round(math.degrees(prev[n].rotation_difference(q).angle),2) for n,q in cur.items()} if prev else {},flush=True);prev=cur
x=json.loads((P/'review/rig_gates.json').read_text());print('WORST',x['Attack']['G6'],flush=True)
