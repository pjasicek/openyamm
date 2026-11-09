from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'grip_contact.py'),run_name='__main__')
sys.argv=['contacts.py','--','Running','Death','Fidget']
runpy.run_path(str(p/'contacts.py'),run_name='__main__')
