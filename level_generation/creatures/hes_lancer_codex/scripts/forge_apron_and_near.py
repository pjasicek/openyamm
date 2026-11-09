import bpy,sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';clips=['Forge_'+r for r in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead')]
sys.argv=['armour_gate.py','--',str(P/'work/forge_complete.blend'),'forge_review',str(S/'armour_forge.json'),*clips];runpy.run_path(str(S/'armour_gate.py'),run_name='__main__')
d=json.loads((P/'review/armour_gate_forge_review.json').read_text());bad=[(c,p,k,v) for c,row in d.items() for p,rs in row.items() for k,v in rs.items() if v[0]>.30];assert not bad,bad
sys.argv=['build_near_lods.py','--','hes_forgemaster'];runpy.run_path(str(S/'build_near_lods.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
