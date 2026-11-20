import bpy,sys,runpy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
# Replace the Hit comparison source with the newly selected professional reaction.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_clips.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
old=bpy.data.actions.get('Hit')
if old:bpy.data.actions.remove(old)
with bpy.data.libraries.load(str(P/'work/round2_hit_source.blend'),link=False)as(src,dst):dst.actions=['HitAlternate']
dst.actions[0].name='Hit';dst.actions[0].use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_clips.blend'))
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
steps=['exported_gates.py','round2_sole_gate.py','round2_elbow_gate.py','skirt_intersections.py','uv_gate.py','extra_gates.py','render_final.py','render_lod_review.py','round2_review.py']
for name in steps:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_dwa1.blend'))
assert hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()==h
(P/'review/round2/gate_run.json').write_text(json.dumps({'runtime_sha256':h,'sample_hz':48,'scripts':steps},indent=2)+'\n')
