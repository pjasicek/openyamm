import runpy,sys,json,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_monk.py')
run('finger_weights.py',p/'work/rig_weights.blend',p/'work/rig_fingers.blend')
roles=json.loads((p/'source/clip_selection.json').read_text())
items=lambda keys:[f'{root}/anim_library/humanoid_set/{roles[k][0]}.glb:{roles[k][1]}:{k}' for k in keys]
run('retarget.py',p/'work/rig_fingers.blend',p/'work/retarget_base.blend',*items(['Standing','Walking','Running','Death','Fidget']))
os.environ['PLANT_FROM']='Standing'
run('retarget.py',p/'work/retarget_base.blend',p/'work/retarget_raw.blend',*items(['Attack','Cast','Hit']))
