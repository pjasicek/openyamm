import bpy,os,sys,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_gate_master.blend'));picks=[f'{n}:{f}'for n in roles for f in range(int(bpy.data.actions[n].frame_range[1])+1)]
run('g4_weights.py',['work/body_gate_master.blend','round1',*picks]);run('g5_hand_stretch.py',['work/body_gate_master.blend',*roles])
for script in ['g6_contacts.py','g6_head_clearance.py','g6_skirt_poke.py']:run(script,['work/body_gate_master.blend',*roles])
run('g6_sword_round1.py',['work/round1/runtime_combined.glb']);run('trace_export.py',['work/round1/runtime_combined.glb',*[f'{r}={P}/work/source_motion_reference.glb:{r}'for r in roles if r!='Dead']]);run('posture_blade_round1.py')
for file in ['g4_round1.json','g5_final.json','g6_contacts.json','g6_fauld.json','g6_trace.json']:shutil.copyfile(P/'work'/file,P/'review/round1'/file)
