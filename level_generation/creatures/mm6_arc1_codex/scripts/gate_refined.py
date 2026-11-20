import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('refine_weights.py',[])
import bpy
acts=[a.name for a in bpy.data.actions if a.use_fake_user]
picks=[f'{a.name}:{f}'for a in bpy.data.actions if a.use_fake_user for f in range(int(a.frame_range[1])+1)]
run('g4_weights.py',['work/rig_twist.blend','refined',*picks])
run('g5_hand_stretch.py',['work/rig_twist.blend',*acts])
run('g6_contacts.py',['work/rig_twist.blend',*acts])
