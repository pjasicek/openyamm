"""Export textured rigid props and economical LODs in fitted world space."""
import bpy,bmesh,sys,os
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/final.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
out=P/'work/props_v2_world';out.mkdir(exist_ok=True)
for part in ('collar','pick','club'):
 src=bpy.data.objects['hes_kept_'+part];objs=[]
 for level,ratio in enumerate((1,.5,.25,.125)):
  o=src.copy();o.data=src.data.copy();o.name=f'{part}_LOD{level}';o.data.name=o.name;bpy.context.scene.collection.objects.link(o);objs.append(o)
  for m in list(o.modifiers):o.modifiers.remove(m)
  o.vertex_groups.clear();o.parent=None;o.matrix_world=Matrix.Identity(4)
  if level:
   for x in bpy.data.objects:x.select_set(x==o)
   bpy.context.view_layer.objects.active=o;m=o.modifiers.new('LOD','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for x in bpy.data.objects:x.select_set(x in objs)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.gltf(filepath=str(out/f'{part}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_extras=True)
 for o in objs:bpy.data.objects.remove(o,do_unlink=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
