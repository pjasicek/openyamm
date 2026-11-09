from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for n,args in [('measure_runtime.py',[]),('loop_probe.py',[]),('g6_sword_surface.py',[p/'export/mm8_m604.blend','Hit','Fidget','Running','Death'])]:
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
