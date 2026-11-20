"""Validate the motion-only revision before producing the selected portable export."""
import bpy,os,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(name):runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('verify_foot_revision.py')
os.environ['M632_CHECK_BLEND']='work/textured_uv.blend'
for name in ('contacts.py','grip_contacts.py'):run(name)
contacts=json.loads((P/'work/contacts.json').read_text())
for name in ('Walking','Running','Attack'):
 for label,v in contacts[name]['contacts'].items():
  if 'depth_m' in v:assert v['depth_m']<(.002 if label.endswith('_hair') else .0015),(name,label,v)
sys.argv=['g4_weights.py','--',str(P/'work/textured_uv.blend'),'foot_revision','Walking:24','Walking:60','Running:22','Running:66','Attack:42','Attack:75','Attack:126','Attack:136','Attack:156']
run('g4_weights.py')
sys.argv=['g5_hand_stretch.py','--',str(P/'work/textured_uv.blend'),'Walking','Running','Attack']
run('g5_hand_stretch.py')
run('export_runtime.py')
