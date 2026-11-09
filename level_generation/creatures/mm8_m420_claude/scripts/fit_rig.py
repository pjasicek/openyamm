"""Compose independent Meshy and measured shell centres, then clone source frames."""
from pathlib import Path
import bpy,bmesh,json,runpy,sys,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
j=json.loads((p/'work/meshy_joints.json').read_text());wr=json.loads((p/'work/wrists.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
def ring(part,z,x):
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[part].data)
 res=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,z),plane_no=(0,0,1))
 vs={v for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge) for v in e.verts if (v.co.x>0)==(x>0)}
 assert len(vs)>=5,(part,z);c=np.mean([v.co[:] for v in vs],axis=0).tolist();bm.free();return c
for sd in ['L','R']:
 j['joints'][sd+'_Hand']=wr[sd];j['joints'][sd+'_Calf']=ring('P04',.535,1 if sd=='L' else -1)
j['joints']['L_Foot']=ring('P06',.14,1)
j['joints']['R_Foot']=ring('P12',.045,-1);j['joints']['R_Toe0']=[j['joints']['R_Foot'][0],j['joints']['R_Foot'][1]-.06,.025]
j['method']='Meshy spine/shoulder/elbow/hips; wrist centres from hand opening loops; knee centres from breeches-only sections; left ankle and right virtual peg-end from their own shell rings. Generic whole-mesh rings rejected because coat/cuff shells and prosthesis invalidate assumptions.'
(p/'work/joints_final.json').write_text(json.dumps(j,indent=2)+'\n')
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/fitted_joints',p/'work/meshy_joints.json')
run('build_rig.py');run('fit_fingers.py',p/'work/rig_v1.blend');run('finger_joints.py',p/'work/rig_v1.blend');run('build_rig.py');run('hand_frame_check.py',p/'work/rig_v1.blend')
for sd in ['R','L']:run('hand_xray.py',p/'work/rig_v1.blend',sd,p/f'review/g3_hand_{sd}')
