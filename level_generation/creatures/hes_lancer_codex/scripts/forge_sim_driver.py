import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['forge_apron_sim.py','--',str(P/'work/forge_heavy_attack.blend'),str(P/'work/forge_apron_sim.blend'),'cloth',*['Forge_'+x for x in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death')]]
runpy.run_path(str(P/'scripts/forge_apron_sim.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
