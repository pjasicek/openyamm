"""Mesh-measured source-frame rig; abort at any failed prerequisite."""
import os,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',['meshy/rig_v1/result_rigged_character_glb_url.glb','work/step1.blend'])
run('arm_rings.py',['work/step1.blend']);
if (P/'work/finger_joints.json').exists():(P/'work/finger_joints.json').rename(P/'work/finger_joints_rejected_ring_tip.json')
run('build_rig.py');run('fit_fingers.py',['work/rig_v1.blend'])
f=json.loads((P/'work/fingers_fit.json').read_text());assert set(f)=={'L','R'}
run('finger_joints.py',['work/rig_v1.blend']);run('build_rig.py');run('hand_frame_check.py',['work/rig_v1.blend'])
