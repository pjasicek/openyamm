import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);L=P.parents[2]/'anim_library/humanoid_set'
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
clips=[('2Hand Axe.glb','2HandAxeIdle','Standing'),('2Hand Axe.glb','2HandAxeWalk','Walking'),('1Hand.glb','MaceAttackR2','Attack'),('2Hand Axe.glb','2HandAxeGetHitF1','Hit')]
run('retarget.py',['work/rig_v1.blend','work/rig_v2.blend',*[f'{L/f}:{c}:{a}' for f,c,a in clips]])
os.environ['FA_RAMP']='.15,.65';run('twist_bones.py',['work/rig_v2.blend','work/rig_v2t.blend']);run('weights_minotaur.py',[]);run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend'])
run('finger_labels_view.py',['work/rig_v4.blend','R','review/finger_labels'])
