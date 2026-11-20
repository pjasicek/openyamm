"""One final contour fit at the actual 88-pixel switch size, with the original installed triangle cap."""
import bpy,os,runpy,sys,json,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';S=P/'scripts';os.environ['FIGC_CONTOUR_REF']=str(R/'switch_height/reference_lod3')
for name in ['refine_far88.py','contour_fit88.py']:runpy.run_path(str(S/name),run_name='__main__')
curve=json.loads((R/'contour_fit88/curve.json').read_text());best=max(curve,key=lambda r:r['pooled_iou']);os.environ['FIGC_REPAIR_SOURCE']=str(R/f"contour_fit88/iteration_{best['iteration']}.blend");runpy.run_path(str(S/'repair_far88.py'),run_name='__main__')
D=R/'far88_bake';E=D/'export_lod3';E.mkdir(parents=True,exist_ok=True)
for n in ['mm6_figc_authoring.blend','mm6_figc_lod0.glb']:shutil.copy2(R/'far_repaired88/export'/n,E/n)
os.environ.update(FIGC_BAKE_ROOT='far88_bake',FIGC_BAKE_LEVEL='3');runpy.run_path(str(S/'rebake_textures.py'),run_name='__main__');subprocess.run(['/usr/bin/python3',str(S/'rebake_review_materials.py'),str(E/'textures')],check=True)
sys.path.insert(0,str(S));import compare_exported_lods as C
C.O=D/'physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True;C.TIER_DIR=E/'textures';C.cal['body_diameter_m']=1.763883397;out=C.render(E/'rebaked.glb',3,'selected');subprocess.run(['/usr/bin/python3',str(S/'measure_reduction.py'),str(R/'switch_height/reference_lod3'),str(out),str(D/'metrics.json')],check=True)
G=D/'gate_input';G.mkdir(exist_ok=True)
for a,b in [('rebaked.glb','mm6_figc_lod0.glb'),('rebaked_authoring.blend','mm6_figc_authoring.blend')]:shutil.copy2(E/a,G/b)
os.environ.update(FIGC_EXPORT_DIR=str(G),FIGC_VALIDATION_DIR=str(D/'validation'));runpy.run_path(str(S/'gates_exported.py'),run_name='__main__')
