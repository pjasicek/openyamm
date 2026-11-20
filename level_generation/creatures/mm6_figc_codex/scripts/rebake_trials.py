"""Geometry-first trials for the revised LOD caps; no accepted exports are replaced."""
import bpy,os,runpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';O=R/'rebake';O.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=O/'renders';C.O.mkdir(exist_ok=True);records=[]
for level,steps in [(0,{'Body':5.,'Axe':4.,'Shield':0.}),(1,{'Body':10.,'Axe':9.,'Shield':8.}),(2,{'Body':18.,'Axe':18.,'Shield':15.}),(3,{'Body':28.,'Axe':25.,'Shield':24.})]:
 parts={}
 for part,step in steps.items():
  os.environ.update(FIGC_REDUCE=f'{part},{level},{step}',FIGC_POLICY='lod_fit',FIGC_SKIP_RENDER='1')
  try:runpy.run_path(str(P/'scripts/rebake_candidate.py'),run_name='__main__')
  except SystemExit as e:assert e.code==0
  tag=f'lod_fit_{part.lower()}_l{level}_s{step:05.2f}'.replace('.','p');parts[part]=tag
 bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'));counts={}
 for part,tag in parts.items():
  with bpy.data.libraries.load(str(R/'candidates'/f'{tag}.blend'),link=False) as (src,dst):dst.meshes=[part+'_reduction_mesh']
  ob=bpy.data.objects[part];ob.data=dst.meshes[0];counts[part]=sum(len(f.vertices)-2 for f in ob.data.polygons)
 path=O/f'lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));E=O/f'export_lod{level}';os.environ.update(FIGC_EXPORT_SOURCE=str(path),FIGC_EXPORT_DIR=str(E));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');out=C.render(E/'mm6_figc_lod0.glb',level,'geometry');m=O/f'geometry_lod{level}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'export_comparison'/f'reference_lod{level}'),str(out),str(m)],check=True);row={'level':level,'parts':counts,'triangles':sum(counts.values()),'metrics':json.loads(m.read_text())};records.append(row);(O/'geometry_curve.json').write_text(json.dumps(records,indent=2));print('GEOMETRY_REBAKE_TRIAL',row,flush=True)
