from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=['check_contacts.py','--',str(p/'work/rig_textured_uv.blend'),'Standing','Walking','Fidget','Hit','Death','Dead']
runpy.run_path(str(p/'scripts/check_contacts.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/verify_export.py'),run_name='__main__')
