"""Export the corrected three-material master with unchanged v4 actions and matching rubble maps."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];W=P/'work/parts_v5'
assert (W/'composition.json').is_file()
bpy.ops.wm.open_mainfile(filepath=str(W/'parts.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();rubble=bpy.data.objects['Rubble']
parts={name:bpy.data.objects[name.title()] for name in ['body','wings','head']}
oldmaterial=rubble.data.materials[0];oldmaterial.name='GargoyleBody_v4'
for part,obj in parts.items():
 mat=obj.data.materials[0];mat.name='Gargoyle'+part.title();mat.use_nodes=True;mat.use_backface_culling=False
 nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(bs.outputs[0],out.inputs['Surface']);bs.inputs['Specular IOR Level'].default_value=.5
 def texture(suffix,space):
  img=bpy.data.images.load(str((P/f'textures/{part}_{suffix}.png').resolve()),check_existing=False);img.colorspace_settings.name=space;n=nt.nodes.new('ShaderNodeTexImage');n.image=img;return n
 bc=texture('basecolor','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
 nm=texture('normal','Non-Color');normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 mr=texture('metal_rough','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=bc
 mat['openyamm_specular']=1.0;mat['openyamm_specular_mask']=True
# Reproject stone-fragment faces onto the corresponding new part, retaining the head UVs.
sources={}
for part in ['body','wings']:
 obj=parts[part];obj.data.calc_loop_triangles();tri=list(obj.data.loop_triangles);co=[v.co.copy() for v in obj.data.vertices]
 sources[part]=(BVHTree.FromPolygons(co,[t.vertices[:] for t in tri],all_triangles=True),tri,co,obj.data.uv_layers.active.data)
oldhead=[p.index for p in rubble.data.polygons if 'Head' in rubble.data.materials[p.material_index].name]
rubble.data.materials.clear()
for part in ['body','head','wings']:rubble.data.materials.append(parts[part].data.materials[0])
uv=rubble.data.uv_layers.active.data;headfaces=set(oldhead);counts={'head':len(headfaces),'body':0,'wings':0}
for face in rubble.data.polygons:
 if face.index in headfaces:face.material_index=1;continue
 part=min(sources,key=lambda p:sources[p][0].find_nearest(face.center)[3]);tree,tris,co,sourceuv=sources[part]
 _,_,ti,_=tree.find_nearest(face.center);source=tris[ti];face.material_index=2 if part=='wings' else 0;counts[part]+=1
 points=[rubble.data.vertices[i].co.copy() for i in face.vertices];mapped=[];distance=0
 for point in points:
  hit,_,fi,dist=tree.find_nearest(point);tr=tris[fi];distance=max(distance,dist)
  mapped.append(barycentric_transform(hit,*[co[i] for i in tr.vertices],*[Vector((*sourceuv[li].uv,0)) for li in tr.loops]))
 mesh_area=(points[1]-points[0]).cross(points[2]-points[0]).length*.5
 uv_area=(mapped[1]-mapped[0]).cross(mapped[2]-mapped[0]).length*.5
 if distance>.006 or uv_area/max(mesh_area,1e-12)<.025 or max((x-y).length for x in mapped for y in mapped)>.13:
  # Fracture interiors use an isotropic stone patch inside a broad wing island, avoiding stretched tiny UV triangles.
  axis=(points[1]-points[0]).normalized();up=face.normal.cross(axis).normalized()
  planar=np.array([[(point-points[0]).dot(axis),(point-points[0]).dot(up)] for point in points])
  extent=max(np.ptp(planar,axis=0).max(),1e-6);planar=(planar-(planar.max(0)+planar.min(0))*.5)/extent*.08
  mapped=[Vector((103.5/1024+u,1-654.5/1024+v,0)) for u,v in planar];face.material_index=2
 for li,value in zip(face.loop_indices,mapped):uv[li].uv=value[:2]
for obj in bpy.data.objects:
 if obj.type=='MESH':obj.hide_render=False
bpy.ops.object.select_all(action='DESELECT')
for obj in parts.values():obj.select_set(True)
bpy.context.view_layer.objects.active=parts['body'];bpy.ops.object.join();body=bpy.context.object;body.name='Gargoyle'
assert len(body.data.polygons)==7247
rig.animation_data.action=bpy.data.actions['Flight'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
selection=[body,rubble,rig]+[o for o in bpy.data.objects if o.name.startswith('Socket_')]
bpy.ops.object.select_all(action='DESELECT')
for obj in selection:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_gar.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_gar_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
(W/'rubble_materials.json').write_text(json.dumps(counts,indent=2));print('EXPORTED_THREE_PARTS',len(body.data.polygons),counts)
