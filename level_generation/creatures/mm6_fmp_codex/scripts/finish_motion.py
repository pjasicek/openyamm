import bpy,bmesh,runpy,sys,json
from pathlib import Path
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_cloth_v3.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
# Opaque ankle-length clothing needs shoes/ankles, not hidden upper-leg cylinders.
bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl] in (5,6) and v.co.z>.22],context='VERTS')
bm.to_mesh(me);bm.free()
with bpy.data.libraries.load(str(p/'work/rig_weighted.blend')) as (d,o):o.objects=['Body']
source=o.objects[0];tree=KDTree(len(source.data.vertices))
for v in source.data.vertices:tree.insert(v.co,v.index)
tree.balance();names={g.index:g.name for g in source.vertex_groups};pieces=[v.value for v in me.attributes['piece'].data]
for v in me.vertices:
 if pieces[v.index]!=0:continue
 _,i,d=tree.find(v.co);assert d<1e-5
 for g in body.vertex_groups:g.remove([v.index])
 for e in source.data.vertices[i].groups:
  if e.weight>1e-6:body.vertex_groups[names[e.group]].add([v.index],e.weight,'REPLACE')
bpy.data.objects.remove(source,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_trimmed.blend'))
sys.argv=['skirt_sim.py','--',str(p/'work/motion_trimmed.blend'),str(p/'work/motion_final.blend'),'Death']
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
for view in ('front','left'):
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_final.blend'),str(p/'review'/('final_clay_'+view)),view,'6','Standing','Walking','Run','Hit','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
sys.argv=['g4_weights.py','--',str(p/'work/motion_final.blend'),'final','Walking:6','Walking:18','Run:6','Run:18','Hit:12','Death:15','Death:30','Death:60']
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
