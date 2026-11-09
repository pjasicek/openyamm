from pathlib import Path
import runpy,sys,shutil
P=Path(__file__).resolve().parents[1]
def run(n,args=()):
 f=P/'scripts'/n;sys.argv=[str(f),'--',*map(str,args)];runpy.run_path(str(f),run_name='__main__')
run('meshy_joints.py',[P/'meshy/rig_v1/result_rigged_character_glb_url.glb',P/'work/step1.blend'])
run('fit_joints.py',[P/'work/step1.blend','Body'])
run('compose_joints.py')
run('build_rig.py')
run('fit_fingers.py',[P/'work/rig_v1.blend'])
run('finger_joints.py',[P/'work/rig_v1.blend'])
run('build_rig.py')
