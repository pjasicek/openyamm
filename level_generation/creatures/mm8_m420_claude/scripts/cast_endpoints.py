import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rows={}
for name,f in [('Standing',0),('Attack',0),('Attack',52.5),('Cast',0),('Cast',52.5)]:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f%1);rows[name+str(f)]={pb.name:pb.matrix.copy() for pb in rig.pose.bones}
ref=rows['Standing0'];out={}
for key,pose in rows.items():
 out[key]={n:{'matrix_max_delta':max(abs(m[i][j]-ref[n][i][j]) for i in range(4) for j in range(4)),'distance_mm':(m.translation-ref[n].translation).length*1000,'rotation_deg':math.degrees(2*math.acos(min(1,abs(m.to_quaternion().normalized().dot(ref[n].to_quaternion().normalized())))))} for n,m in pose.items()}
assert max(v['matrix_max_delta'] for pose in out.values() for v in pose.values())<1e-5
print('ENDPOINTS',json.dumps({k:sorted(v.items(),key=lambda x:x[1]['rotation_deg'],reverse=True)[:6] for k,v in out.items()}),flush=True)
(P/'review/dual_cast/endpoints.json').write_text(json.dumps(out,indent=2))
