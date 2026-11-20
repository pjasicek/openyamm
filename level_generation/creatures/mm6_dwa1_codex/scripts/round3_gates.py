import bpy,sys,runpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
steps=['exported_gates.py','round2_sole_gate.py','round2_elbow_gate.py','round3_locomotion_gate.py','skirt_intersections.py','uv_gate.py','extra_gates.py','render_final.py','render_lod_review.py']
for name in steps:
 path=P/'scripts'/name
 if name.startswith('round2_'):
  source=path.read_text().replace('review/round2/','review/round3/')
  if name=='round2_sole_gate.py':source=source.replace("['Standing','Fidget','Hit','Attack','Walking']","['Standing','Fidget','Hit','Attack']")
  exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
 else:runpy.run_path(str(path),run_name='__main__')
# Reuse the accepted rest-pose close-up setup and add locomotion against the same physical floor grid.
path=P/'scripts/round2_review.py';source=path.read_text().split('# Independent exported-joint traces')[0].replace('review/round2/','review/round3/')
exec(compile(source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
import common
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for role in ['Walking','Running']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(9):
  t=i*.1;f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1)
  common.render_views(str(P/f'review/round3/{role}_{i}'),.34,1.15,views=('front','left','three_quarter'),resolution=(600,600))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_dwa1.blend'))
assert hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()==h
(P/'review/round3/gate_run.json').write_text(json.dumps({'runtime_sha256':h,'sample_hz':48,'scripts':steps},indent=2)+'\n')
