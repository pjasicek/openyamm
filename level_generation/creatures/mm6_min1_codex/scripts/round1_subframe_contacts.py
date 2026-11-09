import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_contacts.py'),run_name='__main__',init_globals={'INPUT':'work/round1_clothed.blend','OUTPUT':'work/round1_subframe_contacts.blend','REPORT':'review/round1/contact_release.json','ROLES':['Attack'],'CREATE_CAST':True,'TIME_FACTOR':1.5})
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__',init_globals={'INPUT':'work/round1_subframe_contacts.blend'})
sys.argv=['g','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_motion_trace.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_blade_audit.py'),run_name='__main__')
