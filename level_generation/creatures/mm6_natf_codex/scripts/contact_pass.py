import runpy,sys,bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('smooth_shoulders.py');roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];picks=[f'{n}:{f}'for n in roles for f in np.arange(0,bpy.data.actions[n].frame_range[1]+.001,bpy.context.scene.render.fps/48)]
run('g4_weights.py',[P/'work/gate_master.blend','smoothed',*picks]);run('prop_contacts.py')
