"""Measure all nine Forgemaster roles before runtime export."""
import bpy,sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts'
src=P/'work/forge_final_fit.blend'
clips=['Forge_'+x for x in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead')]
for name,args in [('gates.py',[src,'forge_review',*clips]),('shell_stretch.py',[src,S/'armour_forge.json','forge_review',*clips]),('shell_leak.py',[src,S/'armour_forge.json','forge_review',*clips]),('armour_gate.py',[src,'forge_review',S/'armour_forge.json',*clips]),('equipment_gate.py',[src,'forge',*clips]),('sole_probe.py',[src,*clips]),('stride.py',[src,'Forge_Walking','Forge_Running']),('jerk_probe.py',[src,'Forge_Attack'])]:
 print('FORGE_VERIFY',name,flush=True);sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
sys.stdout.flush();os._exit(0)
