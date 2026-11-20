"""Reduce rigid low-detail regions after weighting; local UVs retain 2.5x head density."""
from pathlib import Path
import bpy,bmesh,math,sys,json
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped_v1.blend'))
m=bpy.data.objects['Wasp'];rig=bpy.data.objects['Wasp_Rig'];bpy.context.view_layer.objects.active=m
bpy.ops.object.select_all(action='DESELECT');m.select_set(True)
names={g.index:g.name for g in m.vertex_groups};protect=m.vertex_groups.new(name='KeepDetail');ids=[]
joints=np.array([b.head_local[:] for b in rig.data.bones])
for v in m.data.vertices:
 groups=[names[g.group] for g in v.groups if g.weight>.25 and g.group in names]
 if any(n.startswith(('Head','Hand','Claw','Antenna','Mandible','Wing','Sword','Shield')) for n in groups) or min(np.linalg.norm(joints-np.array(v.co),axis=1))<.016:ids.append(v.index)
protect.add(ids,1,'REPLACE');before=sum(len(f.vertices)-2 for f in m.data.polygons)
mod=m.modifiers.new('RegionReduction','DECIMATE');mod.ratio=.63;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name);m.vertex_groups.remove(m.vertex_groups['KeepDetail'])
# Rebuild a closed consistent normal field after local repairs.
bm=bmesh.new();bm.from_mesh(m.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m.data);bm.free()
for idx,mat in enumerate(m.data.materials):
 if mat is None:
  mat=bpy.data.materials.new('WaspBody');m.data.materials[idx]=mat
 if mat.name!='WaspEquipment':mat.name='WaspBody';mat.use_nodes=True;mat.diffuse_color=(.5,.5,.5,1)
body_slot=next(i for i,mat in enumerate(m.data.materials) if mat.name=='WaspBody')
sc=bpy.context.scene;sc.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in m.data.polygons:f.select=f.material_index==body_slot
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.hide(unselected=True)
bpy.ops.uv.smart_project(angle_limit=math.radians(30),island_margin=.002,area_weight=0,scale_to_bounds=False)
scale_head_islands(m,('Head','Mandible_L','Mandible_R'),factor=2.5)
bpy.ops.uv.pack_islands(margin=.002,margin_method='FRACTION',rotate=True,shape_method='CONCAVE')
bpy.ops.mesh.reveal(select=False);bpy.ops.object.mode_set(mode='OBJECT')
m.data.uv_layers.active.name='UVMap'
for v in m.data.vertices:
 weights=sorted(v.groups,key=lambda g:g.weight,reverse=True)
 for g in weights[4:]:m.vertex_groups[g.group].remove([v.index])
 total=sum(g.weight for g in v.groups);assert total>.99
 for g in list(v.groups):m.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
m.data.calc_loop_triangles();tri=np.array([f.vertices[:] for f in m.data.loop_triangles]);uv=np.array([[m.data.uv_layers.active.data[i].uv[:] for i in f.loops] for f in m.data.loop_triangles]);co=np.array([v.co[:] for v in m.data.vertices]);slots=np.array([f.material_index for f in m.data.loop_triangles])
np.savez(P/'work/uv_geometry.npz',co=co,tri=tri,uv=uv,slots=slots)
report=dict(before_triangles=before,after_triangles=len(tri),body_triangles=int(sum(slots==body_slot)),equipment_triangles=int(sum(slots!=body_slot)),head_density_factor=2.5,max_influences=max(len(v.groups) for v in m.data.vertices),materials=[x.name for x in m.data.materials])
assert report['max_influences']<=4 and len(tri)<15000 and np.isfinite(uv).all()
(P/'work/reduction_uv.json').write_text(json.dumps(report,indent=2));print('UV',report)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
obj=m.copy();obj.data=m.data.copy();obj.modifiers.clear();obj.parent=None;obj.vertex_groups.clear();bpy.context.collection.objects.link(obj)
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=body_slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
obj.data.materials.clear()
for f in obj.data.polygons:f.material_index=0
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/m556_body_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE',export_attributes=False)
