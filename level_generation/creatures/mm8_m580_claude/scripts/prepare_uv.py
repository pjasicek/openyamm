"""Preserve the articulated head and flippers, simplify the shell, and unwrap with extra head density."""
from pathlib import Path
import bpy,bmesh,sys,json,math
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));m=bpy.data.objects['Turtle'];rig=bpy.data.objects['Turtle_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bpy.context.view_layer.objects.active=m
names={g.index:g.name for g in m.vertex_groups};protect=m.vertex_groups.new(name='PreserveDeformation');ids=[v.index for v in m.data.vertices if any(names[g.group]!='Shell' and g.weight>.1 for g in v.groups if g.group in names)];protect.add(ids,1,'REPLACE')
before=len(m.data.polygons);dec=m.modifiers.new('ShellReduction','DECIMATE');dec.ratio=.82;dec.vertex_group=protect.name;dec.invert_vertex_group=True;dec.vertex_group_factor=1000;dec.use_collapse_triangulate=True
bpy.ops.object.modifier_move_up(modifier=dec.name);bpy.ops.object.modifier_apply(modifier=dec.name);m.vertex_groups.remove(m.vertex_groups['PreserveDeformation'])
bm=bmesh.new();bm.from_mesh(m.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m.data);bm.free()
for uv in list(m.data.uv_layers):m.data.uv_layers.remove(uv)
m.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(50),island_margin=.004,area_weight=0,scale_to_bounds=False);scale_head_islands(m,('Head','Jaw'),factor=2.5);bpy.ops.uv.pack_islands(margin=.004,margin_method='FRACTION',rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
# Split only the 40 folded projection faces identified by the UV raster audit.
uv_data=m.data.uv_layers.active.data
for i,face in enumerate(json.loads((P/'review/uv_patch_faces.json').read_text())):
 for loop in m.data.polygons[face].loop_indices:uv_data[loop].uv.x+=100+i*2
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(margin=.004,margin_method='FRACTION',rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
m.data.materials.clear();mat=bpy.data.materials.new('TurtleBody');mat.use_nodes=True;mat.diffuse_color=(.5,.5,.5,1);m.data.materials.append(mat)
for f in m.data.polygons:f.material_index=0
m.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in m.data.loop_triangles]);uv=np.array([[m.data.uv_layers.active.data[i].uv[:] for i in t.loops] for t in m.data.loop_triangles]);co=np.array([v.co[:] for v in m.data.vertices]);areas=np.abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]))*.5
assert np.isfinite(uv).all() and min(areas)>1e-12
assert max(len(v.groups) for v in m.data.vertices)<=4
np.savez(P/'work/uv_geometry.npz',co=co,tri=tri,uv=uv,slots=np.zeros(len(tri),np.int32))
report={'before_triangles':before,'after_triangles':len(tri),'vertices':len(co),'head_density_factor':2.5,'padding_fraction':.004,'minimum_uv_area':float(min(areas))};(P/'work/reduction_uv.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
obj=m.copy();obj.data=m.data.copy();obj.modifiers.clear();obj.parent=None;obj.vertex_groups.clear();bpy.context.collection.objects.link(obj);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
(P/'texturing').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/m580_body_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE',export_attributes=False)
print('UV',json.dumps(report),flush=True)
