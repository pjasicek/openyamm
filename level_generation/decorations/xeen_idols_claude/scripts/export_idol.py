"""Stage 4 (Blender): LOD0 + the finished maps -> LOD1-3 (collapse decimation of LOD0, UVs carried) -> GLB with one
material (base colour, normal, metallic-roughness), objects <name>, <name>_LOD1.._LOD3 at the same transform.
Writes work/<id>/<name>_raw.glb; link_static_model_lods.py then links the chain into export/<name>.glb.
Usage: blender -b --python export_idol.py -- <id>"""
import json
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
idol_id = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'idols.json')))[idol_id]
work = os.path.join(PROJECT, 'work', idol_id)
name = cfg['name']
LOD_RATIOS = cfg.get('lod_ratios', [0.5, 0.23, 0.09])
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'low.blend'))
scene = bpy.context.scene
for o in list(scene.objects):
    if o.name != 'LOD0':
        bpy.data.objects.remove(o, do_unlink=True)
low = bpy.data.objects['LOD0']
low.vertex_groups.clear()
for a in [a for a in low.data.attributes if a.name == 'part']:
    low.data.attributes.remove(a)
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
             'visible_shadow'):
    setattr(low, attr, True)
low.name = name
low.data.name = name

mat = bpy.data.materials.new(name + '_stone')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(file, non_color):
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(work, file))
    t.image.name = f'{name}_{file[4:-4]}'
    if non_color:
        t.image.colorspace_settings.name = 'Non-Color'
    return t


tb = tex('map_basecolor.png', False)
nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
tn = tex('map_normal.png', True)
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
tm = tex('map_mr.png', True)
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tm.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mat.use_backface_culling = True
low.data.materials.clear()
low.data.materials.append(mat)


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


counts = [tris(low.data)]
for level, ratio in enumerate(LOD_RATIOS, 1):
    tmp = bpy.data.objects.new('tmp', low.data.copy())
    scene.collection.objects.link(tmp)
    mod = tmp.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=1.047198)
    me.name = f'{name}_LOD{level}'
    ob = bpy.data.objects.new(f'{name}_LOD{level}', me)
    scene.collection.objects.link(ob)
    counts.append(tris(me))
print('LOD_TRIANGLES', counts)
for o in scene.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = low
out = os.path.join(work, f'{name}_raw.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_tangents=False, export_animations=False,
                          export_skins=False, export_morph=False, export_image_format='AUTO', export_apply=True,
                          export_vertex_color='NONE')
json.dump({'lod_triangles': counts}, open(os.path.join(work, 'lods.json'), 'w'))
print('EXPORTED', out)
