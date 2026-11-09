"""Protect the face/hands during a bent-pose reduction and export the complete textured assembly."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];weapon=bpy.data.objects['PolearmMesh'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
bm=bmesh.new();bm.from_mesh(body.data);before=(len(bm.verts),len(bm.faces));bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-10],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');print('REMOVE NON-SURFACE',before,(len(bm.verts),len(bm.faces)));bm.to_mesh(body.data);bm.free()
rest=np.array([v.co[:] for v in body.data.vertices]);parts=np.array([v.value for v in body.data.attributes['part'].data]);original_faces=[list(f.vertices) for f in body.data.polygons];tree=BVHTree.FromPolygons([Vector(v) for v in rest],original_faces,all_triangles=True)
fixed=set(np.where((rest[:,2]>1.90)|((parts!=1)&(np.abs(rest[:,0])<.3))|((np.abs(rest[:,0])>.45)&(rest[:,2]>1.0)))[0].tolist());seen={};uv=body.data.uv_layers.active
for loop in body.data.loops:
 v=loop.vertex_index;u=uv.data[loop.index].uv
 if v in seen and (u-seen[v]).length>1e-6:fixed.add(v)
 seen.setdefault(v,u.copy())
rig.animation_data.action=bpy.data.actions['Death'];sc.frame_set(37);a=body.data.attributes.new('rest_co','FLOAT_VECTOR','POINT');a.data.foreach_set('vector',rest.ravel())
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier='SalamanderSkin')
g=body.vertex_groups.new(name='KeepDetail');g.add(list(fixed),1.,'REPLACE');mod=body.modifiers.new('BentReduction','DECIMATE');mod.ratio=.85;mod.vertex_group=g.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
me=body.data;rc=np.empty(len(me.vertices)*3);me.attributes['rest_co'].data.foreach_get('vector',rc);me.vertices.foreach_set('co',rc);me.attributes.remove(me.attributes['rest_co']);me.normals_split_custom_set([(0.,0.,0.)]*len(me.loops));body.vertex_groups.remove(body.vertex_groups['KeepDetail']);me.update();bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
mod=body.modifiers.new('SalamanderSkin','ARMATURE');mod.object=rig
reverse=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons],all_triangles=True);error=np.array([tree.find_nearest(v.co)[3] for v in me.vertices]+[reverse.find_nearest(Vector(v))[3] for v in rest]);protected=np.array([reverse.find_nearest(Vector(rest[i]))[3] for i in fixed]);print('PROTECTED WORST',[(int(list(fixed)[i]),rest[list(fixed)[i]].tolist(),float(protected[i])) for i in np.argsort(protected)[-5:]],flush=True);assert protected.max()<.001 and np.percentile(error,99)<.004,(protected.max(),np.percentile(error,99))
report={'before_triangles':len(original_faces),'after_triangles':len(me.polygons),'surface_mm_p50_p95_p99_max':(np.percentile(error,[50,95,99,100])*1000).tolist(),'protected_max_mm':float(protected.max()*1000)};(P/'review/checks/reduction.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCTION',report)
for polygon in me.polygons:polygon.use_smooth=True
# Each material uses the same atlas for all tiers; region ramps are attached after export.
def material(name,label):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
 def tex(suffix,space):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'm568_{label}_{suffix}.png'),check_existing=True);node.image.colorspace_settings.name=space;return node
 nt.links.new(tex('basecolor_1k','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_1k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);return mat
for slot,label,name in [(0,'body','Salamander_A'),(1,'head','SalamanderHead_A')]:body.data.materials[slot]=material(name,label)
# Pack the prop's three surface classes into a single compact atlas and material.
bpy.ops.object.select_all(action='DESELECT');weapon.select_set(True);bpy.context.view_layer.objects.active=weapon
if not weapon.data.uv_layers:weapon.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.0,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
for f in weapon.data.polygons:
 name=weapon.data.materials[f.material_index].name;strip=0 if name=='PolearmShaft' else 1 if name=='PolearmSteel' else 2
 for li in f.loop_indices:weapon.data.uv_layers.active.data[li].uv.x=(strip+.04+.92*weapon.data.uv_layers.active.data[li].uv.x)/3
 f.material_index=0
weapon.data.materials.clear();weapon.data.materials.append(material('SalamanderPolearm_A','weapon'))
# Parenting includes the bone tail; measure its inverse at rest to preserve the authored tip.
socket=bpy.data.objects['Socket_Polearm_Tip'];bn='Polearm';parent=rig.matrix_world@rig.pose.bones[bn].matrix@Matrix.Translation((0,rig.data.bones[bn].length,0));socket.matrix_parent_inverse=parent.inverted();socket.matrix_basis=Matrix.Translation((0,0,1.20))
for image in bpy.data.images:
 if image.source=='FILE':image.pack()
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m568.blend'))
body.data.uv_layers.remove(body.data.uv_layers['BodyRetextureUV'])
# One skinned export mesh lets the existing LOD and attachment tools preserve every animation sample.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);weapon.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
for o in bpy.data.objects:o.select_set(o==body or o==rig or o==socket)
bpy.context.view_layer.objects.active=rig;sc.render.fps=48;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m568_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
print('EXPORTED',len(body.data.polygons),len(rig.data.bones),len(bpy.data.actions))
