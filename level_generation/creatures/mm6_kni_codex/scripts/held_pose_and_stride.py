import bpy,sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'))
with bpy.data.libraries.load(str(P/'work/runtime_master.blend')) as (src,dst):
 dst.actions=['Dead']
bpy.data.actions['Dead'].use_fake_user=True
rig=bpy.data.objects['Rig'];bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/body_gate_master.blend'))
a=bpy.data.actions['Walking'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];positions={s:[] for s in 'LR'}
for f in range(25):
 bpy.context.scene.frame_set(f)
 for s in positions:positions[s].append((rig.matrix_world@rig.pose.bones[f'B_{s}_Foot'].head).y)
stride={s:2*(max(v)-min(v)) for s,v in positions.items()};(P/'review/stride.json').write_text(json.dumps({'method':'twice fore-aft foot-head excursion in one Walking cycle','stride_m':stride},indent=2));print('STRIDE',stride)
for n in ['g6_contacts.py','g6_head_clearance.py','g6_skirt_poke.py']:
 sys.argv=[n,'--','work/body_gate_master.blend','Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
