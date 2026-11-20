"""Pre-contact iteration checks; certify the final master with forge_revision_gates.py."""
import bpy,runpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_slam.blend'
for name,args in [('gates.py',[src,'forge_slam','Forge_Attack']),('shell_stretch.py',[src,S/'armour_forge_concept.json','forge_slam','Forge_Attack']),('shell_leak.py',[src,S/'armour_forge_concept.json','forge_slam','Forge_Attack']),('equipment_gate.py',[src,'forge_slam','Forge_Attack']),('armour_gate.py',[src,'forge_slam',S/'armour_forge_concept.json','Forge_Attack'])]:
 os.environ['FSTEP']='.5';sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
sys.stdout.flush();os._exit(0)
