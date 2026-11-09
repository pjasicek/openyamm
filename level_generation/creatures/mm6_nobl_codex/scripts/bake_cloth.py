import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('tabard_rig.py')
os.environ['CLOTH_GROUP']='nobl_cloak'
run('cloak_sim.py',['rig_v7.blend'])
os.environ['CLOTH_GROUP']='nobl_tabard'
run('cloak_sim.py',['rig_v7.blend'])
os.environ['CLOTH_GROUP']='nobl_skirt_back'
run('cloak_sim.py',['rig_v7.blend'])
run('clip_sheet.py',[p/'work/rig_v7.blend',p/'review/clay_cloth','three_quarter','6','Standing','Walking','Running','Attack','Hit','Death','Dead'])
