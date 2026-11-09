from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
path=p/'scripts/check_contacts.py';sys.argv=[str(path),'--',str(p/'work/cage.blend'),'Running'];runpy.run_path(str(path),run_name='__main__')
r=json.loads((p/'review/contacts.json').read_text());assert max([x['depth_m'] for v in r.values() for x in v.values()]+[0])<.002,r
path=p/'scripts/reduce_rigged.py';sys.argv=[str(path),'--'];runpy.run_path(str(path),run_name='__main__')
