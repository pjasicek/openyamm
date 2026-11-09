import bpy,bmesh,json,sys,runpy
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/troll_master.blend'))
o=bpy.data.objects['Troll'];rig=bpy.data.objects['Rig'];me=o.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
print('BOUNDARIES',[(v.index,tuple(v.co)) for v in bm.verts if any(e.is_boundary for e in v.link_edges) and v.co.z>1.35 and abs(v.co.x)<.2][:100])
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
for f in me.polygons:
 if 1.35<f.center.z<1.65 and abs(f.center.x)<.2 and f.center.y<0:
  n=m.polygons[f.index].normal
  if n.dot(f.normal)<0:print('FLIP',f.index,tuple(f.center),tuple(f.normal),tuple(n),list(f.vertices))
ev.to_mesh_clear();bm.free()
sys.path.insert(0,str(p/'scripts'));import common
common.setup_render((700,700));common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/neck_clay'),1.55,.75,('three_quarter','left','front'),target=(0,-.13),resolution=(700,700))
sys.argv=['stride.py','--',str(p/'work/rig_v5.blend'),'Walking','Running'];runpy.run_path(str(p.parent/'mm6_natm_claude/scripts/stride.py'),run_name='__main__')
