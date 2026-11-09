"""Puts a Meshy retexture (meshy/<job>/) on the rigged mesh: work/rig_v7.blend -> work/rig_v8.blend. Checks first that
the returned model kept our UVs (same positions -> same UVs), then builds the 'Mage' material from the base colour,
normal, roughness and metallic maps, and renders textured views. Args: job."""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
job = sys.argv[sys.argv.index('--') + 1]
D = os.path.join(common.PROJECT, 'meshy', job)
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v7.blend'))
mesh = bpy.data.objects['Mage']; me = mesh.data
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(D, 'model_urls_glb.glb'))
ret = next(o for o in set(bpy.data.objects) - before if o.type == 'MESH')
# UV check: the retextured model is our clean export (1.578 m); compare per loop by nearest position (scaled)
rme = ret.data; sc = 1.7 / 1.578
pts = {}
for p in rme.polygons:
    for li in p.loop_indices:
        v = ret.matrix_world @ rme.vertices[rme.loops[li].vertex_index].co * sc
        pts.setdefault((round(v.x, 3), round(v.y, 3), round(v.z, 3)), []).append(tuple(rme.uv_layers.active.data[li].uv))
miss = 0; diff = []
for p in me.polygons:
    for li in p.loop_indices:
        v = mesh.matrix_world @ me.vertices[me.loops[li].vertex_index].co
        k = (round(v.x, 3), round(v.y, 3), round(v.z, 3))
        if k not in pts:
            miss += 1; continue
        uv = me.uv_layers.active.data[li].uv
        diff.append(min(abs(uv[0] - a) + abs(uv[1] - b) for a, b in pts[k]))
print('UVCHECK loops', len(diff), 'unmatched positions', miss, 'max uv diff', round(max(diff), 5) if diff else None,
      'median', round(float(np.median(diff)), 6) if diff else None)
for o in list(set(bpy.data.objects) - before):
    bpy.data.objects.remove(o, do_unlink=True)
mat = bpy.data.materials.new('Mage'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, colorspace, y):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(D, name))
    t.image.colorspace_settings.name = colorspace; t.location = (-400, y); return t


nt.links.new(tex('texture_urls_0_base_color.png', 'sRGB', 300).outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(tex('texture_urls_0_roughness.png', 'Non-Color', 0).outputs['Color'], bsdf.inputs['Roughness'])
nt.links.new(tex('texture_urls_0_metallic.png', 'Non-Color', -300).outputs['Color'], bsdf.inputs['Metallic'])
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('texture_urls_0_normal.png', 'Non-Color', -600).outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
me.materials.clear(); me.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v8.blend'))
arm = bpy.data.objects['Mage_Rig']; arm.animation_data.action = bpy.data.actions['Idle_9']
s = bpy.context.scene; s.frame_set(0); common.workbench_clay(s, textured=True)
common.render_views(os.path.join(common.REVIEW, f'{job}_full'), 0.9, 2.0, views=('front', 'three_quarter', 'left', 'back'), resolution=(500, 700))
common.render_views(os.path.join(common.REVIEW, f'{job}_head'), 1.53, 0.42, views=('front', 'three_quarter', 'left'), resolution=(400, 400))
