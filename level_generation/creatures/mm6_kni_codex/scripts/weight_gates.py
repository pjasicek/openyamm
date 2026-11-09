import sys,os,runpy,bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('armour_weights.py');run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend'])
run('apply_grip.py',['work/rig_v4.blend','work/rig_v6.blend']);run('clip_timing.py')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
picks=[f'{n}:{f}' for n in roles for f in range(int(bpy.data.actions[n].frame_range[0]),int(bpy.data.actions[n].frame_range[1])+1)]
run('g4_weights.py',['work/rig_v6t.blend','all_frames',*picks])
run('g6_contacts.py',['work/rig_v6t.blend',*roles])
run('g6_head_clearance.py',['work/rig_v6t.blend',*roles])
