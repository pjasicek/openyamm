from pathlib import Path
import json,subprocess,sys,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];r=P/'review/round7';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
d,b=read_glb(P/'export/mm6_dwa1.glb');a=next(a for a in d['animations']if a['name']=='Running');errors=[]
for ch in a['channels']:
 ar=accessor_array(d,b,a['samplers'][ch['sampler']]['output']);errors.append(float(abs(ar[-1]-ar[0]).max()))
assert max(errors)==0
weights=[]
for m in d['meshes']:
 for pr in m['primitives']:
  at=pr['attributes'];ks=[k for k in at if k.startswith('WEIGHTS_')]
  if ks:weights.append({'mesh':m['name'],'max_sum_error':float(abs(sum(accessor_array(d,b,at[k]).astype(float).sum(1)for k in ks)-1).max())})
assert max(x['max_sum_error']for x in weights)<1e-4
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
(r/'final_numeric.json').write_text(json.dumps({'runtime_sha256':h,'Running_loop_max_endpoint_error':max(errors),'skin_weights':weights,'stride_length':.89,'Running_duration_s':.8,'run_multiplier':1.55,'nominal_model_speed_m_s':.89/.8*1.55},indent=2))
q=subprocess.run([sys.executable,'output/codex_batch/check_bindings.py',str(P/'integration/actors.yml')],text=True,capture_output=True);(r/'bindings_check.json').write_text(json.dumps({'runtime_sha256':h,'exit_code':q.returncode,'stdout':q.stdout,'stderr':q.stderr},indent=2));print(q.stdout,flush=True);assert q.returncode==0 and 'BAD'not in q.stdout+q.stderr
url=sys.argv[1]
for name,cmd in [('viewer_check',['node','level_generation/creatures/claude_shared/check_viewer.mjs',url,'30']),('playback_check',['node',str(P/'scripts/check_playback.mjs'),url,'60'])]:
 q=subprocess.run(cmd,text=True,capture_output=True);(r/(name+'.json')).write_text(json.dumps({'runtime_sha256':h,'exit_code':q.returncode,'stdout':q.stdout,'stderr':q.stderr},indent=2));print(name,q.returncode,flush=True);assert q.returncode==0
print('Validation receipts bound to',h,flush=True)
