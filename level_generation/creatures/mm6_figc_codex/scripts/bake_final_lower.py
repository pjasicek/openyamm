"""Bake, export, measure and run rig gates for the capped lower LODs."""
import bpy,os,runpy,sys,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';D=R/'final_lower';D.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
sources={1:R/'lod1_refit/lod1.blend',2:R/'far_fit_correct/lod2.blend',3:R/'far_repaired88/lod3.blend'};reports={}
os.environ.update(FIGC_REDUCE='Body,1,11',FIGC_POLICY='far_final',FIGC_SKIP_RENDER='1')
try:runpy.run_path(str(P/'scripts/far_candidate.py'),run_name='__main__')
except SystemExit as error:assert error.code==0
bpy.ops.wm.open_mainfile(filepath=str(R/'far_fit_correct/lod1.blend'))
with bpy.data.libraries.load(str(R/'candidates/far_final_body_l1_s11p00.blend'),link=False) as (src,dst):dst.meshes=['Body_reduction_mesh']
bpy.data.objects['Body'].data=dst.meshes[0];(R/'lod1_refit').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(R/'lod1_refit/lod1.blend'))
os.environ['FIGC_REPAIR_SOURCE']=str(R/'contour_fit88/iteration_1.blend');runpy.run_path(str(P/'scripts/repair_far88.py'),run_name='__main__')
for level,path in sources.items():
 E=D/f'export_lod{level}';os.environ.update(FIGC_EXPORT_SOURCE=str(path),FIGC_EXPORT_DIR=str(E));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');os.environ.update(FIGC_BAKE_ROOT='final_lower',FIGC_BAKE_LEVEL=str(level));runpy.run_path(str(P/'scripts/rebake_textures.py'),run_name='__main__');subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_review_materials.py'),str(E/'textures')],check=True)
 C.O=D/'physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True;C.cal['body_diameter_m']=1.763883397;C.TIER_DIR=R/'reference_tier_textures';reference=C.render(R/'before/export/mm6_figc_lod0.glb',level,'reference');C.TIER_DIR=E/'textures';candidate=C.render(E/'rebaked.glb',level,'selected');mp=C.O/f'metrics_lod{level}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(reference),str(candidate),str(mp)],check=True)
 G=D/f'gate_input{level}';G.mkdir(exist_ok=True);shutil.copy2(E/'rebaked.glb',G/'mm6_figc_lod0.glb');shutil.copy2(E/'rebaked_authoring.blend',G/'mm6_figc_authoring.blend');os.environ.update(FIGC_EXPORT_DIR=str(G),FIGC_VALIDATION_DIR=str(D/f'validation{level}'));runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__');m=json.loads(mp.read_text());reports[str(level)]={'source':str(path.relative_to(P)),'image_metrics':m,'gates':json.loads((D/f'validation{level}/export_full_gates.json').read_text())};(D/'reports.json').write_text(json.dumps(reports,indent=2));print('LOWER_LOD_BAKED',level,flush=True)
