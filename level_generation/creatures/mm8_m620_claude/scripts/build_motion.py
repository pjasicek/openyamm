from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
src=root/'level_generation/creatures/mm6_pman_claude_20261013/export/mm6_pman_v2.glb'
roles=['Standing','Walking','Fidget','Hit','Death','Dead']
run('retarget.py',p/'work/rig_v1.blend',p/'work/motion_v1.blend',*[str(src)+':'+role+':'+role for role in roles])
run('twist_bones.py',p/'work/motion_v1.blend',p/'work/motion_twist.blend')
run('finger_weights.py',p/'work/motion_twist.blend',p/'work/weighted_v1.blend')
