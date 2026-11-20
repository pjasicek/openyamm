import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import candidate_gates as g
results={}
for level in range(4):
 results[str(level)]=g.run(P/f'work/final_lod{level}.blend',f'lod{level}');(P/'review/final/all_gates.json').write_text(json.dumps(results,indent=2))
