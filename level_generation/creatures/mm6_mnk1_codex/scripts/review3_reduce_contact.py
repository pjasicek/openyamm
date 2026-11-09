import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];dest=p/'work/g6_contacts.json';before=dest.read_bytes()
try:
 sys.argv=['g6_contacts.py','--',str(p/'work/candidate_0.95.blend'),'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__');(p/'review/round3/reduction/candidate_0.95_g6_contacts.json').write_bytes(dest.read_bytes())
finally:dest.write_bytes(before)
