import os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['CHECK_BLEND']='work/gated_master.blend';os.environ['CHECK_PREFIX']='final'
for n in ['finalize_motion.py','check_pilots.py','check_contacts.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
assert max(v['depth_m'] for x in json.loads((P/'review/final_contacts.json').read_text()).values() for v in x.values())<.002
for n in ['export_runtime.py','verify_export.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
