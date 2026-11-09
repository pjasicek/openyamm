import bpy,runpy,json,subprocess,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1'
sel=json.loads((P/'review/reduction_soft/selection.json').read_text())
for level,row in sel.items():row['blend']=f'work/round1/lod{level}.blend';row['textures']=str(P/'work/round1/textures/lod0')
(P/'review/reduction_soft/selection.json').write_text(json.dumps(sel,indent=2))
for level in range(1):subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(P/'work/round1/textures/lod0')],check=True)
runpy.run_path(str(P/'scripts/export_levels.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/pack_runtime.py')],check=True)
notes=(P/'integration/playbook_notes.md').read_text()
subprocess.run(['/usr/bin/python3',str(P/'scripts/prepare_review.py')],check=True)
(P/'integration/playbook_notes.md').write_text(notes)
