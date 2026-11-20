import sys,runpy,json,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];ref=json.loads((p/'source/clip_selection.json').read_text());ref['Running']=ref['Walking'];ref['Dead']=ref['Death']
sys.argv=['trace_export.py','--',str(p/os.environ.get('TRACE_GLB','export/mm6_mnk1.glb'))]+[f'{n}={p.parents[2]}/anim_library/humanoid_set/{s}.glb:{c}' for n,(s,c) in ref.items()]
runpy.run_path(str(p/'scripts/trace_export.py'),run_name='__main__')
