import os,sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
rom=json.loads((p/'work/rom.json').read_text())
picks=[f"{v['role']}:{max(0,v['frame']-1)}" for v in rom['stress_poses']]
run('g4_weights.py',[p/'work/rig_v5.blend','source_rom',*picks])
run('prepare_clips.py')
run('clip_timing.py')
os.environ['TWIST_POSE_ONLY']='1'
run('twist_bones.py',[p/'work/rig_v6t.blend',p/'work/rig_v6t.blend'])
del os.environ['TWIST_POSE_ONLY']
run('cloak_rig.py')
run('bake_cloth.py')
