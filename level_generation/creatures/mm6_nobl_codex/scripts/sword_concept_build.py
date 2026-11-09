import runpy,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(p/'scripts'))
for name in ['sword_concept.py','export_runtime.py']:
 sys.argv=[name];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
subprocess.run(['python3',str(repo/'tools/prepare_actor_glb.py'),str(p/'export/mm6_nobl_lod0.glb'),str(p/'export/mm6_nobl_runtime_lod0.glb')],check=True)
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
for name in ['package_runtime.py','export_audit.py','sword_concept_invariants.py']:
 subprocess.run(['python3',str(p/'scripts'/name)],check=True)
sys.argv=['sword_concept_check.py'];runpy.run_path(str(p/'scripts/sword_concept_check.py'),run_name='__main__')
