"""Run the explicit, project-local Blender steps listed in work/selected_steps.json."""
from pathlib import Path
import json,os,sys,runpy
p=Path(__file__).resolve().parents[1]
os.chdir(p)
for step in json.loads((p/'work/selected_steps.json').read_text()):
 script=(p/'scripts'/step['script']).resolve()
 assert script.is_relative_to(p/'scripts') and script.is_file(), script
 prior=dict(os.environ)
 os.environ.update(step.get('env',{}))
 sys.argv=[str(script),'--',*step.get('args',[])]
 print('STEP',script.name,flush=True)
 runpy.run_path(str(script),run_name='__main__')
 os.environ.clear();os.environ.update(prior)
