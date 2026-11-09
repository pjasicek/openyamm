from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
a=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
run('g4_skirt.py',[p/'work/rig_v5t.blend',*a])
run('g6_skirt_poke.py',[p/'work/rig_v5t.blend',*a])
run('g6_contacts.py',[p/'work/rig_v5t.blend',*a])
run('g6_head_clearance.py',[p/'work/rig_v5t.blend',*a])
run('g5_hand_stretch.py',[p/'work/rig_v5t.blend',*a])
run('g4_weights.py',[p/'work/rig_v5t.blend','authored','Standing:0','Walking:6','Running:6','Attack:16','Attack:20','Attack:24','Attack:28','Hit:6','Fidget:15','Death:14','Death:28'])
for view in ('front','left','three_quarter'):
 run('clip_sheet.py',[p/'work/rig_v5t.blend',p/'review'/('authored_'+view),view,7,'Standing','Fidget','Death'])
