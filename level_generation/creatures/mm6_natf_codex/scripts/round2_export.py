import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=P/'scripts/final_ground.py'
exec(compile(s.read_text().replace('work/pre_final_ground.blend','work/round2_cloth.blend').replace('dz=max(dz,.002-low)',"dz=max(dz,(.007 if name in ['Death','Dead'] else .002)-low)"),str(s),'exec'))
drop=P/'scripts/round2_drop_shield.py'
exec(compile(drop.read_text().replace('work/round2_cloth.blend','work/accepted_master.blend'),str(drop),'exec'))
runpy.run_path(str(P/'scripts/round2_opening.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
