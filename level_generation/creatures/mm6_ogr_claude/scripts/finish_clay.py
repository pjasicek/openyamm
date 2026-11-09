from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/cloth.py'),run_name='__main__')
for name in ['g4_skirt.py','g6_skirt_poke.py']:
 s=p/'scripts'/name;sys.argv=[str(s),'--',str(p/'work/rig_v5t.blend'),'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'];runpy.run_path(str(s),run_name='__main__')
runpy.run_path(str(p/'scripts/export_clay.py'),run_name='__main__')
