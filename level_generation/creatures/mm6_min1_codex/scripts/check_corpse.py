import runpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts'
sys.argv=['rig_gates_corpse.py','--','work/production_master.blend'];runpy.run_path(str(S/'rig_gates_corpse.py'),run_name='__main__')
d=json.loads((P/'review/rig_gates_corpse.json').read_text());assert all(all(v['pass'].values()) for v in d.values()),{k:v['pass'] for k,v in d.items()}
old=json.loads((P/'review/rig_gates.json').read_text());old.update(d);(P/'review/rig_gates.json').write_text(json.dumps(old,indent=2))
