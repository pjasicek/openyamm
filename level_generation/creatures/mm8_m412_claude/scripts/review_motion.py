import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
acts=['Standing','Walking','Running','Attack','Hit','Fidget','Death']
run('g5_hand_stretch.py',p/'work/rig_v5.blend',*acts)
run('sole_probe.py',p/'work/rig_v5.blend',*acts)
for view in ['front','left','three_quarter']:
 run('clip_sheet.py',p/'work/rig_v5.blend',p/('review/motion_v1_'+view),view,'7',*acts)
run('rpg_preview.py',repo/'anim_library/humanoid_set/Unarmed.glb',p/'review/g1_hit','three_quarter','7','UnarmedGetHitF1')
