import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as R
bpy.ops.wm.open_mainfile(filepath=str(P/'work/authoring_high.blend'));R.reset();report={}
for name,kind in [('Body','body'),('SpearMesh','spear'),('BucklerMesh','buckler')]:
 o=bpy.data.objects[name];report[name]={'before':R.triangles(o),'protection':R.protect(o,kind)};R.reduce(o,.5 if kind=='body'else .72,True);report[name]['after']=R.triangles(o)
print('PROBE',json.dumps(report),flush=True);(P/'review/reduction').mkdir(exist_ok=True);(P/'review/reduction/probe.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduced_probe.blend'))
print('ENGINES',bpy.context.scene.render.bl_rna.properties['engine'].enum_items.keys(),flush=True)
