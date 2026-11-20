import sys,json,runpy,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;runner=P.parent/'claude_shared/gates/run_gates.py'
c=json.loads((P/'gates.json').read_text())
for label,root in [('final',P)]:
 config=copy.deepcopy(c)
 for prop in config['props']:prop['file']=str(root/prop['file'])
 path=P/f'review/round4/shared_{label}_config.json';path.write_text(json.dumps(config,indent=2));out=P/f'review/round4/shared_{label}'
 sys.argv=[str(runner),'--',str(root/'export/mm6_arc1.glb'),'--config',str(path),'--out',str(out)]
 try:runpy.run_path(str(runner),run_name='__main__')
 except (SystemExit,RuntimeError) as e:
  result=json.loads((out/'gates.json').read_text());assert result['status']in ['FAIL','UNVERIFIED'],result;print('SHARED_RUNNER',label,result['status'],str(e),flush=True)
