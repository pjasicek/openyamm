"""Build the first motion/weight pilot from the fitted source-frame rig."""
from pathlib import Path
import runpy, sys
p=Path(__file__).resolve().parents[1]; root=p.parents[2]
def run(n, args):
    script=p/'scripts'/n; sys.argv=[str(script),'--',*[str(a) for a in args]]
    runpy.run_path(str(script),run_name='__main__')
w=p/'work'; lib=root/'anim_library'; hs=lib/'humanoid_set'
run('rom_extract.py', [f'Attack={hs}/1Hand.glb:SwordAttackR6',f'Walking={hs}/Armed.glb:ArmedWalk',f'Hit={hs}/Unarmed.glb:UnarmedGetHitF1',f'Death={hs}/Armed.glb:ArmedDeath1'])
run('grip_from_source.py',[hs/'1Hand.glb','SwordAttackR6:0','SwordAttackR6:6','SwordAttackR6:12'])
run('retarget.py',[w/'rig_v1.blend',w/'motion_set.blend',f'{hs}/1Hand.glb:SwordAttackR6:Attack',f'{hs}/Armed.glb:ArmedWalk:Walking',f'{hs}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{hs}/Armed.glb:ArmedDeath1:Death'])
run('retarget_mixamo.py',[w/'motion_set.blend',w/'motion_raw.blend',f'{lib}/mixamo/Standard Idle.fbx:Standing',f'{lib}/mixamo/Standing Taunt Battlecry.fbx:Fidget:plant',f'{lib}/mixamo/Standard Run.fbx:Running'])
run('twist_bones.py',[w/'motion_raw.blend',w/'twisted.blend'])
run('weights_fix.py',[w/'twisted.blend',w/'weighted.blend'])
run('finger_weights.py',[w/'weighted.blend',w/'fingered.blend'])
