import sys, runpy, os
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(P/'scripts'))
def run(name,*args):
    sys.argv=[name,'--',*map(str,args)]
    runpy.run_path(str(P/'scripts'/name),run_name='__main__')
for side in ('R','L'):run('hand_xray.py',P/'work/rig_v1.blend',side,P/f'review/g3_hand_{side}')
L=next((ROOT/'anim_library').glob('*/1Hand.glb')).parent
MX=ROOT/'anim_library/mixamo'
run('retarget.py',P/'work/rig_v1.blend',P/'work/rig_v2s.blend',f'{L}/Armed.glb:ArmedIdle:GripRef')
run('retarget_mixamo.py',P/'work/rig_v2s.blend',P/'work/rig_v2.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Walk.fbx:Walking',f'{MX}/Sword And Shield Slash.fbx:Attack:plant',f'{MX}/Sword And Shield Slash.fbx:AttackFull:turn')
run('twist_bones.py',P/'work/rig_v2.blend',P/'work/rig_v2t.blend')
run('weights_fix.py',P/'work/rig_v2t.blend',P/'work/rig_v3.blend')
run('finger_weights.py',P/'work/rig_v3.blend',P/'work/rig_v4.blend')
os.environ['GRIP_RENDER']=str(P/'review/g5_grip')
run('grip_solve.py',P/'work/rig_v4.blend','GripRef',8)
run('apply_grip.py',P/'work/rig_v4.blend',P/'work/pilot.blend')
for view in ('front','left','three_quarter'):
    run('clip_sheet.py',P/'work/pilot.blend',P/f'review/pilot_{view}',view,7,'Standing','Walking','Attack')
