import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
r=check(P/'work/master.blend');(P/'review/round3_baseline_gates.json').write_text(json.dumps(r,indent=2));print('ALL_GATES',r['passed']);assert r['passed'],r
