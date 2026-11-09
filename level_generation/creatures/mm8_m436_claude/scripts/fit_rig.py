from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('compose_joints.py')
jpath=p/'work/joints_final.json';j=json.loads(jpath.read_text())
# The forward-set Ogre skull pivots inside its neck ring, not behind the hair.
j['joints']['Head']=[-.02934,-.205,1.46098]
j['report']['head_pivot']='Shifted forward to the measured skull/neck center; Meshy placed the pivot at the back of the hair.'
jpath.write_text(json.dumps(j,indent=2)+'\n')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')
for side in ('R','L'):run('hand_xray.py',p/'work/rig_v1.blend',side,p/f'review/fingers_{side}')
