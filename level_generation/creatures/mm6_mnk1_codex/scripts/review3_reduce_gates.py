import bpy,runpy,os,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round3/reduction';os.environ['GATE_BLEND']='work/candidate_0.85.blend'
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];files=['review/round3/penetration.json','work/review1_occlusion.json','work/g6_contacts.json'];before={f:(p/f).read_bytes() for f in files}
try:
 for script,file in zip(['review3_penetration.py','review1_occlusion.py','g6_contacts.py'],files):
  if script=='g6_contacts.py':sys.argv=[script,'--',str(p/os.environ['GATE_BLEND'])]+roles
  try:runpy.run_path(str(p/'scripts'/script),run_name='__main__')
  except AssertionError as e:print('REDUCTION_GATE_FAILED',script,str(e)[:300],flush=True)
  (out/('candidate_0.85_'+Path(file).name)).write_bytes((p/file).read_bytes())
finally:
 for f,data in before.items():(p/f).write_bytes(data)
