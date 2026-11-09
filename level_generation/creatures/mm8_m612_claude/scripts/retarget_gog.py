from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1];R=P.parents[2]
script=P/'scripts/retarget.py'
clips=[('Armed','ArmedCastRAttackHand1','Attack'),('Armed','ArmedCastRAttackHand1','Cast'),('Armed','ArmedWalk','Walking'),('Unarmed','UnarmedRunForward','Running'),('Unarmed','UnarmedGetHitF1','Hit'),('Unarmed','UnarmedDeath1','Death')]
sys.argv=[str(script),'--',str(P/'work/rig_fingers.blend'),str(P/'work/animated_raw.blend')]+[str(R/f'anim_library/humanoid_set/{lib}.glb')+':'+clip+':'+role for lib,clip,role in clips]
runpy.run_path(str(script),run_name='__main__')

script=P/'scripts/retarget_mixamo.py'
sys.argv=[str(script),'--',str(P/'work/animated_raw.blend'),str(P/'work/animated_raw.blend'),str(R/'anim_library/mixamo/Standard Run.fbx')+':Running']
runpy.run_path(str(script),run_name='__main__')
