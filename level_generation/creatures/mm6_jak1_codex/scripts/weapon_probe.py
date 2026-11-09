import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];series=[]
for f in np.arange(0,act.frame_range[1]+.001,scene.render.fps/48):
 scene.frame_set(int(f),subframe=float(f-int(f)));M=rig.matrix_world@rig.pose.bones['Staff'].matrix;series.append((float(f/scene.render.fps),np.array(M)))
rows=[]
for deg in range(0,360,5):
 q=np.array(Matrix.Rotation(math.radians(deg),3,'Z'));tip=q@np.array([.055,0,.76]);edge=q@np.array([1.,0,0]);flat=q@np.array([0.,1,0]);ts=np.array([(m@np.r_[tip,1])[:3]for _,m in series]);v=np.diff(ts,axis=0)*48;speed=np.linalg.norm(v,axis=1);fwd=np.array([-(m[:3,:3]@np.array([0,0,1.]))[1]for _,m in series[:-1]]);ok=fwd>.5;k=int(np.argmax(np.where(ok,speed,0)));E=series[k][1][:3,:3]@edge;F=series[k][1][:3,:3]@flat;ve=float(v[k]@E);vf=float(v[k]@F);rows.append({'roll_deg':deg,'impact_s':(series[k][0]+series[k+1][0])/2,'speed_mps':float(speed[k]),'target_dot':float(fwd[k]),'signed_edge_lead':ve/max(speed[k],1e-9),'edge_share':abs(ve)/max(math.hypot(ve,vf),1e-9)})
(P/'work/staff_roll_sweep.json').write_text(json.dumps(rows,indent=2));print('WEAPON CURRENT',rows[0]);print('WEAPON BEST',max(rows,key=lambda x:x['signed_edge_lead']),flush=True)
