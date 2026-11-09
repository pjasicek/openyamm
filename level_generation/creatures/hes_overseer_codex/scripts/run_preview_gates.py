"""Run the shared exported-mesh gates, preserving their exit code and avoiding the sandbox audio shutdown hang."""
import importlib.util,json,os,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];shared=P.parent/'claude_shared/gates/run_gates.py'
spec=importlib.util.spec_from_file_location('shared_creature_gates',shared);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
path=P/'work/overseer_body_lod0.glb';glb=g.Glb(path);config=json.loads((P/'gates_overseer.json').read_text())
for side in 'LR':
 hn=glb.rest[glb.names[f'B_{side}_Hand']];wrist=hn[:3,3]
 # Measured knuckle plane, matching the shared gate's five-finger anatomical convention.
 a=glb.rest[glb.names[f'B_{side}_Finger1']][:3,3]-wrist
 b=glb.rest[glb.names[f'B_{side}_Finger5']][:3,3]-wrist
 normal=np.cross(a,b);normal/=np.linalg.norm(normal)
 normal*=1 if side=='R' else -1
 config['hands'][side]['palm_axis']=(np.linalg.inv(hn[:3,:3])@normal).tolist()
(P/'gates_overseer.json').write_text(json.dumps(config,indent=2)+'\n')
sys.argv=[str(shared),str(path),'--config',str(P/'gates_overseer.json'),'--out',str(P/'review/gates_candidate')]
import runpy
code=0
try:runpy.run_path(str(shared),run_name='__main__')
except SystemExit as e:code=int(e.code or 0)
except RuntimeError as e:
 print(str(e),flush=True);code=2
except BaseException:
 import traceback
 traceback.print_exc();code=1
print('SHARED_GATES_FINISHED',code,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(code)
