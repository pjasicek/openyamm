import bpy,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n,args in [('weights_monk.py',[]),('finger_weights.py',[p/'work/rig_weights.blend',p/'work/rig_fingers.blend'])]:
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_fingers.blend'))
b=bpy.data.objects['Body'];names=[g.name for g in b.vertex_groups];weights=[[(names[g.group],g.weight) for g in v.groups] for v in b.data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'));b=bpy.data.objects['Body'];assert len(b.data.vertices)==len(weights)
b.vertex_groups.clear()
for n in names:b.vertex_groups.new(name=n)
for i,gs in enumerate(weights):
 for n,w in gs:b.vertex_groups[n].add([i],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/retarget_raw.blend'))
runpy.run_path(str(p/'scripts/pilot_finish.py'),run_name='__main__')
