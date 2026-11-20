import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
sys.argv=['retarget_mixamo.py','--','work/rig_uv.blend','work/rig_death.blend',str(P.parents[2]/'anim_library/mixamo/Standing React Death Backward.fbx')+':DeathBackward']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
sys.argv=['apply_grip.py','--','work/rig_death.blend','work/rig_actions.blend'];runpy.run_path(str(P/'scripts/apply_grip.py'),run_name='__main__')
