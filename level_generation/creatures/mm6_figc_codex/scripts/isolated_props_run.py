import bpy,os,runpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';O=R/'isolated_props';sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
os.environ['FIGC_BAKE_ROOT']='isolated_props';runpy.run_path(str(P/'scripts/rebake_textures.py'),run_name='__main__')
D=O/'export_lod0';subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_review_materials.py'),str(D/'textures')],check=True);C.O=O/'physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True;C.TIER_DIR=D/'textures';out=C.render(D/'rebaked.glb',0,'rebaked');subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'rebake/physical/reference_lod0'),str(out),str(C.O/'metrics.json')],check=True)
import shutil
G=O/'gate_input';G.mkdir(exist_ok=True);shutil.copy2(D/'rebaked.glb',G/'mm6_figc_lod0.glb');shutil.copy2(D/'rebaked_authoring.blend',G/'mm6_figc_authoring.blend');os.environ.update(FIGC_EXPORT_DIR=str(G),FIGC_VALIDATION_DIR=str(O/'validation'));runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__')

Q=O/'details';Q.mkdir(exist_ok=True);os.environ.update(FIGC_PROP_VALIDATION=str(O/'validation/export_validation.blend'),FIGC_PROP_TIERS=str(D/'textures'),FIGC_PROP_REVIEW=str(Q));runpy.run_path(str(P/'scripts/render_props_r3.py'),run_name='__main__')
