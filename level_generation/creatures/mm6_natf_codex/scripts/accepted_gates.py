import runpy,sys,bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('grip_radius.py');roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];picks=[f'{n}:{f}'for n in roles for f in np.arange(0,bpy.data.actions[n].frame_range[1]+.001,bpy.context.scene.render.fps/48)]
run('g4_weights.py',[P/'work/accepted_master.blend','accepted',*picks]);run('g5_hand_stretch.py',[P/'work/accepted_master.blend',*roles]);run('audit_accepted.py');run('review_accepted.py')
g4=json.loads((P/'work/g4_accepted.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());cloth=json.loads((P/'review/cloth/accepted_geometry_audit.json').read_text())
assert max(v['stretch_p99']for d in g4.values()for v in d.values())<=2
assert max(v['max_edge_stretch']for d in g5.values()for v in d.values())<=4.5
assert max(d['cloth_penetration']['mm']for d in cloth.values())<=.5
print('ACCEPTED G4 G5 CLOTH PASS',flush=True)
