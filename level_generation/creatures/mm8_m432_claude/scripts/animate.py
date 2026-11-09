"""Retarget the selected professional clips onto the measured source-frame rig."""
import bpy,sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
MX=ROOT/'anim_library/mixamo';L=ROOT/'anim_library/humanoid_set'
def run(script,*args):
    print('RUN',script,flush=True);sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
run('retarget.py',P/'work/rig_v1.blend',P/'work/rig_set.blend',f'{L}/2Hand Sword.glb:2HandSwordIdle:GripRef')
clips={'Standing':'Great Sword Idle (4).fbx','Walking':'Great Sword Walk.fbx','Running':'Great Sword Run.fbx','Attack':'Great Sword Slash (4).fbx','Hit':'Great Sword Impact (3).fbx','Death':'Two Handed Sword Death.fbx','Cast':'Spell Cast.fbx'}
run('retarget_mixamo.py',P/'work/rig_set.blend',P/'work/rig_motion.blend',*[f'{MX}/{file}:{name}' + (':plant' if name in ('Attack','Hit') else ':turn' if name=='Cast' else '') for name,file in clips.items()])
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',P/'work/rig_motion.blend',P/'work/rig_twist.blend')
run('weights_fix.py',P/'work/rig_twist.blend',P/'work/rig_weighted.blend')
os.environ['FRADIUS']='0.014'
run('finger_weights.py',P/'work/rig_weighted.blend',P/'work/rig_fingers.blend')
