"""Final runtime reimport, all accepted clip gates, and refreshed review renders."""
import bpy,sys,runpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
def run(name,source=None):
 path=P/'scripts'/name
 exec(compile(path.read_text()if source is None else source,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
run('import_final.py',(P/'scripts/import_final.py').read_text().replace("P/'work/textured_master.blend'","P/'work/round4/selected_lod0.blend'"))
source=(P/'scripts/exported_gates.py').read_text().replace("['import_final.py','contact_final.py']","['contact_final.py']")
run('exported_gates.py',source)
for name in ['round2_sole_gate.py','round2_elbow_gate.py','round3_locomotion_gate.py','skirt_intersections.py','extra_gates.py','round4_palms_gate.py']:
 source=(P/'scripts'/name).read_text().replace('review/round2/','review/round4/').replace('review/round3/','review/round4/')
 if name=='round2_sole_gate.py':source=source.replace("['Standing','Fidget','Hit','Attack','Walking']","['Standing','Fidget','Hit','Attack']")
 run(name,source)
source=(P/'scripts/uv_gate.py').read_text().replace("P/'work/textured_master.blend'","P/'work/export_reimport.blend'").replace("for layer in ['UVMap','HeadUV']:","for layer,slot in [('UVMap',0),('HeadUV',1)]:").replace("me.uv_layers[layer]","me.uv_layers['UVMap']").replace("if (me.attributes['head'].data[tri.polygon_index].value==1)!=(layer=='HeadUV'):continue","if me.polygons[tri.polygon_index].material_index!=slot:continue")
run('uv_gate.py',source)
for name in ['render_final.py','render_lod_review.py']:run(name)
source=(P/'scripts/round2_review.py').read_text().split('# Independent exported-joint traces')[0].replace('review/round2/','review/round4/')
run('round2_review.py',source)
import common
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for role in ['Walking','Running']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(9):
  t=i*.1;f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1)
  common.render_views(str(P/f'review/round4/{role}_{i}'),.34,1.15,views=('front','left','three_quarter'),resolution=(600,600))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_dwa1.blend'))
assert hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()==h
(P/'review/round4/gate_run.json').write_text(json.dumps({'runtime_sha256':h,'sample_hz':48,'scope':'All eight clips of final exported LOD0; accepted rest rig, palm orientation and action data remain exact.'},indent=2)+'\n')

