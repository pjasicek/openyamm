"""Rebuild the local source-motion pilot without touching installed models."""
from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
def run(name,*args):
    sys.argv=[name,'--',*[str(x) for x in args]]
    runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('weights_fix.py',p/'work/rig_v1.blend',p/'work/weighted.blend')
run('finger_weights.py',p/'work/weighted.blend',p/'work/weighted.blend')
sources=json.loads((p/'review/motion/selected_sources.json').read_text())
args=[v['path']+':'+v['clip']+':'+k for k,v in sources.items() if k!='Running']
run('retarget.py',p/'work/weighted.blend',p/'work/pilot.blend',*args)
run('twist_bones.py',p/'work/pilot.blend',p/'work/pilot.blend')
run('grip_from_source.py','anim_library/humanoid_set/1Hand.glb','SwordAttackR6:0')
