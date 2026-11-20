from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
b=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=b.data
me.materials.clear()
for name,job,uvname in [('Centaur','body_texture_v1','UVMap'),('CentaurHead','head_texture_v1','HeadUV')]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
    uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map=uvname
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/'meshy'/job/'texture_urls_0_base_color.png'));nt.links.new(uv.outputs['UV'],tx.inputs['Vector']);nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
for p in me.polygons:p.material_index=me.attributes['head'].data[p.index].value
# Raster inputs preserve original topology and both UV layouts for texture class masks.
me.calc_loop_triangles();tri=list(me.loop_triangles)
np.savez_compressed(P/'work/uv3d.npz',vertices=np.array([v.co[:]for v in me.vertices]),faces=np.array([t.vertices[:]for t in tri]),head=np.array([me.attributes['head'].data[t.polygon_index].value for t in tri]),component=np.array([v.value for v in me.attributes['component'].data]),uv=np.array([[me.uv_layers['UVMap'].data[l].uv[:]for l in t.loops]for t in tri]),head_uv=np.array([[me.uv_layers['HeadUV'].data[l].uv[:]for l in t.loops]for t in tri]))
