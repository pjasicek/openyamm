import bpy,json,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';sys.dont_write_bytecode=True;bpy.ops.wm.open_mainfile(filepath=str(W/'lod3.blend'));report={}
for name in ['Body','BowAsset']:
 ob=bpy.data.objects[name];before=sum(len(f.vertices)-2 for f in ob.data.polygons);changed=ob.data.validate(verbose=True,clean_customdata=False);ob.data.update();report[name]={'changed':changed,'triangles_before':before,'triangles_after':sum(len(f.vertices)-2 for f in ob.data.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=str(W/'lod3.blend'));(P/'review/round2/reduction/mesh_cleanup.json').write_text(json.dumps(report,indent=2));print('CLEANUP',report,flush=True)
code=(P/'scripts/round2_distance_recheck.py').read_text().replace('for level in [1,2,3]:','for level in [3]:');exec(compile(code,str(P/'scripts/round2_distance_recheck.py'),'exec'),{'__file__':str(P/'scripts/round2_distance_recheck.py'),'__name__':'__main__'})
runpy.run_path(str(P/'scripts/round2_distance_export.py'),run_name='__main__')
