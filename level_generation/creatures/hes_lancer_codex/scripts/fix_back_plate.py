"""Keep the short lower-back ceramic panel within its stretch budget; rerun its shell gates."""
import bpy
from pathlib import Path
import runpy, sys
P=Path(__file__).resolve().parents[1]; S=P/'scripts'
clips=['Carbine_Standing','Carbine_Walking','Lancer_Running','Carbine_Attack','Carbine_Hit','Carbine_Fidget','Carbine_Death','Carbine_Dead']
sys.path.insert(0,str(S))
runpy.run_path(str(S/'armour_spec_lancer.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lancer_pre_backplate.blend'))
old=bpy.data.objects['Arm_back_low']
weights=[{old.vertex_groups[e.group].name:e.weight for e in v.groups} for v in old.data.vertices]
for name in ('lancer_polished','lancer_complete'):
    path=P/f'work/{name}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    ob=bpy.data.objects['Arm_back_low']
    for group in list(ob.vertex_groups):ob.vertex_groups.remove(group)
    groups={n:ob.vertex_groups.new(name=n) for n in set().union(*weights)|{'B_Spine'}}
    for i,row in enumerate(weights):
        row={n:w*.6 for n,w in row.items()}
        row['B_Spine']=row.get('B_Spine',0)+.4
        row={n:w for n,w in row.items() if w>=.03}
        total=sum(row.values())
        for n,w in row.items():groups[n].add([i],w/total,'REPLACE')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
for name,args in [('shell_stretch.py',[S/'armour_lancer.json','lancer',*clips]),('shell_leak.py',[S/'armour_lancer.json','lancer',*clips]),('armour_gate.py',['lancer',S/'armour_lancer.json',*clips])]:
    sys.argv=[name,'--',str(P/'work/lancer_complete.blend'),*map(str,args)]
    runpy.run_path(str(S/name),run_name='__main__')
