import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['apply_materials.py','cloth_gate.py']:runpy.run_path(str(p/n),run_name='__main__')
sys.argv=['g6','--',str(p.parent/'work/textured.blend'),'Attack'];runpy.run_path(str(p/'g6_contacts.py'),run_name='__main__')
