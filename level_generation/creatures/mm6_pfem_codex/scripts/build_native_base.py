import bpy,sys,runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];s=p/'scripts'
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(s/name),run_name='__main__')
run('weights_pfem.py',p/'work/grounded_pilots.blend',p/'work/grounded_body.blend')
run('finger_weights.py',p/'work/grounded_body.blend',p/'work/grounded_weighted.blend')
run('author_native_stance.py')
os.environ['PLANT_FROM']='Standing'
run('retarget.py',p/'work/native_base.blend',p/'work/all_raw.blend','anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1:Hit')
os.environ.pop('PLANT_FROM')
