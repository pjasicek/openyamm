import bpy,runpy,os,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round4';os.environ['GATE_BLEND']=os.environ.get('CANDIDATE','work/review4_tri.blend')
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];files=['work/gates_dense.json','review/round3/penetration.json','work/g6_contacts.json'];before={f:(p/f).read_bytes() for f in files}
try:
 for script,file in zip(['gates_dense.py','review3_penetration.py','g6_contacts.py'],files):
  if script=='g6_contacts.py':sys.argv=[script,'--',str(p/os.environ['GATE_BLEND'])]+roles
  try:runpy.run_path(str(p/'scripts'/script),run_name='__main__')
  except AssertionError as e:print('REDUCTION_GATE_FAILED',script,str(e)[:300],flush=True)
  (out/(os.environ.get('TRIAL_TAG','tri')+'_'+Path(file).name)).write_bytes((p/file).read_bytes())
finally:
 for f,data in before.items():(p/f).write_bytes(data)
