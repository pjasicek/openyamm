import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
for n in ['equip_bow.py','floor_bow.py','gate_equipment.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
sys.argv=['transfer_uv.py','--','work/rig_equipped.blend','meshy/body_retexture_v1','work/rig_textured.blend'];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
