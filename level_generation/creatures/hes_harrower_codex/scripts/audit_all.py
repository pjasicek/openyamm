from pathlib import Path
import sys,runpy,bpy
P=Path(__file__).resolve().parents[1]
blend=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(blend));clips=[a.name for a in bpy.data.actions if a.name.startswith('Harrower_')]
for script,args in [('gates.py',[str(blend),'current',*clips]),('jerk_probe.py',[str(blend),*[c for c in clips if not c.endswith('_Dead')]]),('stride.py',[str(blend),'Harrower_Walking','Harrower_Running']),('audit_geometry.py',[str(blend),'current','.25']),('armour_gate.py',[str(blend),'current',str(P/'scripts/armour_harrower.json'),*clips]),('shell_leak.py',[str(blend),str(P/'scripts/armour_harrower.json'),'current',*clips])]:
 print('AUDIT',script,flush=True);sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
