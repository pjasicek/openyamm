"""Reduce the accepted triangle mesh and keep labelled, animated masters for every LOD gate."""
import bpy,json,sys,os,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];rows=[]
for level,ratio in [(1,.54),(2,.24),(3,.0999)]:
 if os.environ.get('LOD_LEVEL') and level!=int(os.environ['LOD_LEVEL']):continue
 bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b;names=[g.name for g in b.vertex_groups];base_count=sum(len(f.vertices)-2 for f in b.data.polygons)
 protect=None
 if level==3:
  a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();bands=np.floor(coords[:,2]/.025).astype(int);ids=set()
  for band in np.unique(bands):
   row=np.where(bands==band)[0]
   for angle in np.arange(8)*math.pi/4:ids.add(int(row[np.argmax(coords[row,:2]@np.array([math.cos(angle),math.sin(angle)]))]))
  r.animation_data.action=None
  for pb in r.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update();protect=b.vertex_groups.new(name='_LOD_outline');protect.add(sorted(ids),.85,'REPLACE')
 mod=b.modifiers.new('Fitted switch-size LOD','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
 if protect:mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=.25
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 if level==3:b.vertex_groups.remove(b.vertex_groups['_LOD_outline'])
 assert names==[g.name for g in b.vertex_groups]
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 if level==3:
  # The coarse robe no longer needs the always-covered shoe roof above the hem.
  for v,pi in zip(b.data.vertices,b.data.attributes['piece'].data):
   if pi.value in [7,8]:v.co.z=min(v.co.z,.045)

 count=sum(len(f.vertices)-2 for f in b.data.polygons);print("COUNT",count,flush=True);assert count<=min([6212,2235,744][level-1],base_count*[.55,.25,.10][level-1])
 bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/review4_lod{level}.blend'))
 for obj in bpy.context.scene.objects:obj.select_set(obj in [r,b])
 bpy.context.view_layer.objects.active=r;bpy.ops.export_scene.gltf(filepath=str(p/f'work/review4_lod{level}.geometry.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
 rows.append(dict(level=level,ratio=ratio,triangles=count,master=f'work/review4_lod{level}.blend'));print('LOD',rows[-1],flush=True)
(p/'review/round4/lod_generation.json').write_text(json.dumps(rows,indent=2))
