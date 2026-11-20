import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as S
rows=[]
for level in range(4):
 row=S.gates(P/f'work/reduction/selected_lod{level}.blend',f'final_lod{level}');rows.append(row);print('FINAL COMBINED LOD',level,row,flush=True)
(P/'review/final_selected_gates.json').write_text(json.dumps(rows,indent=2))
runpy.run_path(str(P/'scripts/final_intent.py'),run_name='__main__')
assert all(r['pass']for r in rows),'A final selected surface failed'
