import bpy,runpy,json,subprocess,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1'
sel=json.loads((P/'review/reduction_soft/selection.json').read_text())
for level,row in sel.items():row['blend']=f'work/round2/lod{level}.blend';row['textures']=str(P/'work/round2/textures')
(P/'review/reduction_soft/selection.json').write_text(json.dumps(sel,indent=2))
subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(P/'work/round2/textures')],check=True)
runpy.run_path(str(P/'scripts/export_levels.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/pack_runtime.py')],check=True)
notes=(P/'integration/playbook_notes.md').read_text()
subprocess.run(['/usr/bin/python3',str(P/'scripts/prepare_review.py')],check=True)
(P/'integration/playbook_notes.md').write_text(notes)
runpy.run_path(str(P/'scripts/round2_gate_regions.py'),run_name='__main__')
