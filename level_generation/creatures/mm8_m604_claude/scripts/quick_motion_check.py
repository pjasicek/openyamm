from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for n,args in [('export_parity.py',[]),('source_rotation_probe.py',[]),('sole_probe.py',[p/'work/ready_final.blend','Walking','Running','Attack','Hit','Death']),('g6_sword_surface.py',[p/'export/mm8_m604.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget'])]:
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
