"""Run the mandatory authoring gates against the same concept-revision master."""
from pathlib import Path
import runpy,sys,os,json
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_final_clearance.blend';tag='forge_concept'
os.environ['FSTEP']='.5'
clips=['Forge_'+x for x in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead')]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if args:clips=['Forge_'+x for x in args]
for name,a in [('gates.py',[src,tag,*clips]),('shell_stretch.py',[src,S/'armour_forge_concept.json',tag,*clips]),('shell_leak.py',[src,S/'armour_forge_concept.json',tag,*clips]),('equipment_gate.py',[src,tag,*clips]),('armour_gate.py',[src,tag,S/'armour_forge_concept.json',*clips])]:
 print('GATE',name,flush=True);sys.argv=[name,'--',*map(str,a)];runpy.run_path(str(S/name),run_name='__main__')
if not args:
 sys.argv=['forge_slam_gate.py','--',src.name];runpy.run_path(str(S/'forge_slam_gate.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
