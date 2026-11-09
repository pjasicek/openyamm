import bpy,os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));bpy.data.objects['KnightPlate'].name='Body';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_gate_master.blend'))
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];picks=[f'{n}:{f}' for n in roles for f in range(int(bpy.data.actions[n].frame_range[1])+1)]
run('g4_weights.py',['work/final_gate_master.blend','final',*picks]);run('g5_hand_stretch.py',['work/final_gate_master.blend',*roles])
# Body-only rest rig for contacts; its geometry/weights and animations equal the exported body.
run('g6_contacts.py',['work/production_body.blend',*filter(lambda n:n!='Dead',roles)]);run('g6_head_clearance.py',['work/production_body.blend',*filter(lambda n:n!='Dead',roles)])
run('g6_skirt_poke.py',['work/production_body.blend',*filter(lambda n:n!='Dead',roles)]);run('g6_sword_mesh.py',['export/mm6_kni_runtime_lod0.glb']);run('trace_export.py',['export/mm6_kni_runtime_lod0.glb',*[f'{r}={P}/work/source_motion_reference.glb:{r}' for r in roles if r!='Dead']]);run('posture_blade.py')
