"""Apply the dedicated head maps to the unchanged head geometry and retain the animated master."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v2.blend'))
mesh=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
# Compare the service head return against the static submission before applying any maps.
loaded=[]
for file in ['texturing/wyrm_head_neutral.glb','meshy/head_texture_v1/model_urls_glb.glb']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/file));objs=set(bpy.data.objects)-before
 obj=max((o for o in objs if o.type=='MESH'),key=lambda o:len(o.data.polygons));loaded.append((obj,objs))
a,b=[x[0] for x in loaded];ac=np.array([a.matrix_world@v.co for v in a.data.vertices]);bc=np.array([b.matrix_world@v.co for v in b.data.vertices]);scale=np.ptp(ac,axis=0).max()/np.ptp(bc,axis=0).max();bc=(bc-(bc.min(0)+bc.max(0))/2)*scale+(ac.min(0)+ac.max(0))/2
kd=kdtree.KDTree(len(b.data.polygons))
for f in b.data.polygons:kd.insert(Vector(bc[list(f.vertices)].mean(0)),f.index)
kd.balance();uv_error=0;corner_error=0
for f in a.data.polygons:
 _,j,_=kd.find(Vector(ac[list(f.vertices)].mean(0)));g=b.data.polygons[j]
 for li,vi in zip(f.loop_indices,f.vertices):
  ds=np.linalg.norm(bc[list(g.vertices)]-ac[vi],axis=1);k=int(ds.argmin());corner_error=max(corner_error,float(ds[k]));uv_error=max(uv_error,(a.data.uv_layers.active.data[li].uv-b.data.uv_layers.active.data[g.loop_indices[k]].uv).length)
assert corner_error<.0001 and uv_error<1/2048,(corner_error,uv_error)
(P/'checks/head_texture_uv_parity.json').write_text(json.dumps({'corner_error_m':corner_error,'uv_error_texels_2k':uv_error*2048,'geometry':'unchanged'},indent=2)+'\n')
for _,objs in loaded:
 for o in objs:bpy.data.objects.remove(o,do_unlink=True)
mat=mesh.data.materials[1];mat.node_tree.nodes.clear();nt=mat.node_tree;bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
def tex(file,space):
 im=bpy.data.images.load(str(T/file));im.colorspace_settings.name=space;im.pack();n=nt.nodes.new('ShaderNodeTexImage');n.image=im;return n
bc=tex('wyrm_head_basecolor_graded.png','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
nm=tex('wyrm_head_normal_1k.png','Non-Color');normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.6;nt.links.new(nm.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
mr=tex('wyrm_head_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);mat['openyamm_specular']=1.0;mat['openyamm_specular_mask']=True
# Two disconnected tail scraps were floating outside the silhouette; remove those generated debris only.
bm=bmesh.new();bm.from_mesh(mesh.data);part=bm.verts.layers.int['part'];verts=[v for v in bm.verts if v[part] in (10,11)];removed=len(verts);bmesh.ops.delete(bm,geom=verts,context='VERTS');bm.to_mesh(mesh.data);bm.free();assert removed==34
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master_v2.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o in (mesh,rig) or o.name.startswith('Socket_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_wyrm_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('MATERIALS',len(mesh.data.polygons),'triangles; removed floating debris',removed)
