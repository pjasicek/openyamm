"""Sequential per-part visual reduction curve; all project writes retain the workspace lease."""
import json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/'review/round3'
sys.path.insert(0,str(ROOT/'tools'))
from creature_workspace import project_guard
TOKEN=os.environ['FIGC_TOKEN'];curve=[];selected={}
for level in range(4):
 for part in ['Body','Axe','Shield']:
  last=None
  for step in range(24):
   tag=f'{part.lower()}_l{level}_s{step:02d}';meta=R/'candidates'/f'{tag}.json';metrics=R/'candidates'/f'{tag}_metrics.json'
   if not meta.exists():
    env=dict(os.environ,FIGC_REDUCE=f'{part},{level},{step}')
    result=subprocess.run([str(ROOT/'tools/run_creature_blender.sh'),'--token',TOKEN,str((P/'scripts/reduction_candidate.py').relative_to(ROOT))],env=env,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
   if not metrics.exists():
    subprocess.run(['python3',str(ROOT/'tools/creature_workspace.py'),'run','--project',str(P),'--token',TOKEN,'--','python3',str(P/'scripts/measure_reduction.py'),str(R/'renders'/f'{part.lower()}_l{level}_s00'),str(R/'renders'/tag),str(metrics)],check=True,stdout=subprocess.DEVNULL)
   row=json.loads(meta.read_text());m=json.loads(metrics.read_text());row.update(tag=tag,minimum_iou=m['minimum_iou'],minimum_ssim=m['minimum_ssim'],visual_pass=m['pass']);curve.append(row)
   if m['pass']:last=tag
   else:
    assert last is not None
    selected[f'{part}_LOD{level}']=last
   with project_guard(P,TOKEN):
    (R/'curve.json').write_text(json.dumps({'curve':curve,'selected':selected},indent=2)+'\n')
   print(json.dumps({k:row[k] for k in ['tag','triangles','minimum_iou','minimum_ssim','visual_pass']}),flush=True)
   if not m['pass']:break
  else:raise RuntimeError('No failing step found for '+part)
print('VISUAL_SEARCH_COMPLETE',json.dumps(selected),flush=True)
