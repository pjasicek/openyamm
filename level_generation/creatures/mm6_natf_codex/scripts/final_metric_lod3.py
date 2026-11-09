import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import equipped_reduction as eq
sel=json.loads((P/'review/reduction_selected.json').read_text());row=eq.trial(3,'final',{n:sel[n]['3']for n in sel});f=P/'review/final/reduction.json';d=json.loads(f.read_text());d['3']=row;f.write_text(json.dumps(d,indent=2));assert row['pass']
