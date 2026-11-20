"""Verify the retained UVs, apply shared maps, export portable authoring and runtime inputs."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
mesh=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_texture_v1/model_urls_glb.glb'))
src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons))
target=np.array([v.co[:] for v in mesh.data.vertices]);source=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices])
scale=np.ptp(target,axis=0).max()/np.ptp(source,axis=0).max()
source=source*scale+(target.max(0)+target.min(0))/2-(source.max(0)+source.min(0))/2*scale
tree=kdtree.KDTree(len(src.data.polygons))
for f in src.data.polygons:tree.insert(Vector(source[list(f.vertices)].mean(0)),f.index)
tree.balance();worst=0;uv_error=0;errors=[]
for f in mesh.data.polygons:
    _,j,dist=tree.find(Vector(target[list(f.vertices)].mean(0)));sf=src.data.polygons[j];worst=max(worst,dist)
    for li,vi in zip(f.loop_indices,f.vertices):
        ds=np.linalg.norm(source[list(sf.vertices)]-target[vi],axis=1);k=int(ds.argmin());worst=max(worst,float(ds[k]));errors.append(float(ds[k]))
        uv_error=max(uv_error,(mesh.data.uv_layers.active.data[li].uv-src.data.uv_layers.active.data[sf.loop_indices[k]].uv).length)
# The texture return welds tiny slivers; keep our geometry and require sub-pixel UV agreement.
assert worst<.001 and uv_error<1/2048,(worst,uv_error)
(P/'checks/texture_uv_parity.json').write_text(json.dumps({'faces':len(mesh.data.polygons),'geometry_error':worst,'uv_error':uv_error,'uv_error_texels_2k':uv_error*2048,'corner_error_percentiles':np.percentile(errors,[50,95,99,100]).tolist(),'source_faces':len(src.data.polygons),'retained_geometry':'unchanged authoring mesh'},indent=2)+'\n')
for o in list(bpy.data.objects):
    if o not in before:bpy.data.objects.remove(o,do_unlink=True)
mat=bpy.data.materials.new('Wyrm');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
def texture(file,space):
    im=bpy.data.images.load(str(T/file));im.colorspace_settings.name=space;im.pack()
    n=nt.nodes.new('ShaderNodeTexImage');n.image=im;return n
bc=texture('wyrm_basecolor_graded.png','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
nm=texture('wyrm_normal_1k.png','Non-Color');normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
mr=texture('wyrm_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
mat['openyamm_specular']=1.0;mat['openyamm_specular_mask']=True
mesh.data.materials.clear();mesh.data.materials.append(mat)
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o in (mesh,rig) or o.name.startswith('Socket_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_wyrm_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
    export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',
    export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('EXPORTED',P/'export/mm6_wyrm_lod0.glb')
