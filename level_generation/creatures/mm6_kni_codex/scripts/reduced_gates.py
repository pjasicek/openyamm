import sys,os,runpy,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('reduce_body.py');run('clay_export.py')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
picks=[f'{n}:{f}' for n in roles for f in range(int(bpy.data.actions[n].frame_range[0]),int(bpy.data.actions[n].frame_range[1])+1)]
run('g4_weights.py',['work/clay.blend','reduced_all',*picks])
run('g5_hand_stretch.py',['work/clay.blend',*roles])
run('g6_contacts.py',['work/production_body.blend',*filter(lambda n:n!='Dead',roles)])
run('g6_head_clearance.py',['work/production_body.blend',*filter(lambda n:n!='Dead',roles)])
run('g6_sword_mesh.py',['work/knight_clay.glb'])
