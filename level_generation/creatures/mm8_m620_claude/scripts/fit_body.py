from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('source_rest.py',root/'anim_library/humanoid_set/Relax.glb')
run('proportions.py','source',root/'anim_library/humanoid_set/Relax.glb')
run('meshy_joints.py',p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend')
run('arm_rings.py',p/'work/step1.blend')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/fitted_joints',p/'work/meshy_joints.json')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
