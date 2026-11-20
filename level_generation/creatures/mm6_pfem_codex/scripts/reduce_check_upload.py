import bpy,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];s=p/'scripts'
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(s/n),run_name='__main__')
run('reduce_rigged.py',p/'work/skirt_animated.blend',p/'work/reduced.blend')
run('finish_geometry.py')
run('g4_weights.py',p/'work/reduced.blend','body','Standing:0','Walking:6','Hit:5','Death:48','Death:71')
run('g5_hand_stretch.py',p/'work/reduced.blend','Standing','Walking','Hit','Death','Fidget')
run('g6_contacts.py',p/'work/reduced.blend','Standing','Walking','Hit','Death','Fidget')
run('cloth_clearance.py')
run('final_cloth_contacts.py')
run('export_uploads.py')
