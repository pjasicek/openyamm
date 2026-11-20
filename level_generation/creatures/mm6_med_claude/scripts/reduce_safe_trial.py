"""Protected reduction trials on the weighted, textured mesh; no new unwrap or retexture."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1];report={}
for ratio,label in [(.93,'13857_safe')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_v2.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data
 reference=np.array([v.co[:] for v in me.vertices]);faces=[list(f.vertices) for f in me.polygons];parts=np.array([v.value for v in me.attributes['part'].data]);tree=BVHTree.FromPolygons([Vector(v) for v in reference],faces,all_triangles=True)
 if ratio<1:
  rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update()
  bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
  skin=next(m for m in body.modifiers if m.type=='ARMATURE');body.modifiers.remove(skin)
  fixed=set(np.where(np.isin(parts,[1,4,101,104,106,100,110,114,119,127,129,130,131,132]))[0].tolist())
  fixed.update(np.where((parts>=100)|np.isin(parts,[1,4,6,9])|((parts==0)&(reference[:,2]>1.28)))[0].tolist())
  first_uv={};uv=me.uv_layers.active
  for loop in me.loops:
   v=loop.vertex_index;u=uv.data[loop.index].uv
   if v in first_uv and (u-first_uv[v]).length>1e-6:fixed.add(v)
   first_uv.setdefault(v,u.copy())
  protect=body.vertex_groups.new(name='ProtectedReduction');protect.add(list(fixed),1.,'REPLACE')
  mod=body.modifiers.new('ProtectedReduction','DECIMATE');mod.ratio=ratio;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
  me=body.data;body.vertex_groups.remove(body.vertex_groups['ProtectedReduction']);me.update()
  bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
  mod=body.modifiers.new('MedusaSkin','ARMATURE');mod.object=rig
 me.calc_loop_triangles();co=np.array([v.co[:] for v in me.vertices]);p2=np.array([v.value for v in me.attributes['part'].data]);reverse=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons],all_triangles=True)
 errors=np.array([tree.find_nearest(v.co)[3] for v in me.vertices]+[reverse.find_nearest(Vector(v))[3] for v in reference]);head_errors=np.array([reverse.find_nearest(Vector(v))[3] for v in reference[np.isin(parts,[1,4,101,104,106])]])
 # Texture corners must remain finite and existing islands retain positive triangle area.
 uv=me.uv_layers.active;uvarea=[]
 for tr in me.loop_triangles:
  a=np.array([uv.data[i].uv[:] for i in tr.loops]);uvarea.append(abs(np.linalg.det(np.column_stack([a[1]-a[0],a[2]-a[0]])))*.5)
 assert np.isfinite(uvarea).all() and min(uvarea)>1e-12
 assert head_errors.max()<.001,'Protected face/hands changed'
 report[label]={'triangles':len(me.loop_triangles),'body_triangles':sum(t.material_index==0 for t in me.loop_triangles),'head_triangles':sum(t.material_index==1 for t in me.loop_triangles),'surface_mm_p50_p95_p99_max':(np.percentile(errors,[50,95,99,100])*1000).tolist(),'protected_max_mm':float(head_errors.max()*1000),'uv_min_area':min(uvarea)}
 rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/f'reduction_{label}.blend'))
 with bpy.data.libraries.load(str(P/'revisions/v1/export/mm6_med.blend'),link=False) as (src,dst):dst.materials=['Medusa_A','MedusaHead_A']
 for i,m in enumerate(dst.materials):body.data.materials[i]=m
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(P/'review/viewer'/f'comparison_{label}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
 print('REDUCTION',label,report[label])
(P/'review/reduction_safe_v2.json').write_text(json.dumps(report,indent=2)+'\n')
