"""Fit source frames using Meshy axial joints and the mesh's wrist/ankle rings."""
import bpy,bmesh,json,numpy as np,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)]
 return runpy.run_path(str(p/'scripts'/name),run_name='__main__')
ns=run('fit_joints.py',p/'work/step1.blend','Body')
M=json.load(open(p/'work/meshy_joints.json'))['joints'];J=dict(M)
for side in ('R','L'):
 q=np.array(M[side+'_Foot']);ring=ns['nearest_ring'](q,(0,0,1),q);assert ring is not None
 J[side+'_Foot']=ring[0].tolist()
bpy.ops.wm.open_mainfile(filepath=str(p/'work/assembled_parts.blend'))
for side,name in [('R','P03'),('L','P04')]:
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
 ring=list({v for e in bm.edges if e.is_boundary for v in e.verts if v.co.z>.985})
 J[side+'_Hand']=np.mean([v.co[:] for v in ring],axis=0).tolist();bm.free()
for side in ('R','L'):
 print('FINAL_LIMB',side,{k:[round(v,4) for v in J[side+'_'+k]] for k in ('UpperArm','Forearm','Hand','Foot')})
json.dump({'height_m':1.89958,'joints':J,'sources':'Meshy axial/shoulder/elbow/hip/knee; skin ankle rings at Meshy height; hand wrist boundary loops excluding tiny knuckle seam'},open(p/'work/joints_final.json','w'),indent=2)
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/g3_joints',p/'work/meshy_joints.json')
if (p/'work/finger_joints.json').exists(): (p/'work/finger_joints.json').unlink()
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
fit=json.load(open(p/'work/fingers_fit.json'));assert set(fit)=={'L','R'},'Finger connectivity fit incomplete'
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')

runpy.run_path(str(p/'scripts/review_hands.py'),run_name='__main__')
