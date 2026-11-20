import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import equipped_reduction as eq
sel=json.loads((P/'review/reduction_selected.json').read_text());report={}
for level in range(4):
 eq.trial(level,'source',None);row=eq.trial(level,'final',{n:sel[n][str(level)]for n in sel});report[str(level)]=row
(P/'review/final/reduction.json').write_text(json.dumps(report,indent=2));assert all(r['pass']for r in report.values())
