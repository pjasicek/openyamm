import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_contacts.py'),run_name='__main__',init_globals={'INPUT':'work/round1_clothed.blend','OUTPUT':'work/round1_contact_final.blend','REPORT':'review/round1/contact_final.json','ROLES':['Attack'],'CREATE_CAST':True})
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__',init_globals={'INPUT':'work/round1_contact_final.blend'})
sys.argv=['gate','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
