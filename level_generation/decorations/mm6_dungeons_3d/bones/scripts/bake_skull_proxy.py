"""Low-poly skull for the instanced skull pile: a UV sphere (SEGMENTS x RINGS) fitted to the Meshy skull's bounds and
shrink-wrapped onto it, with its own Smart UV layout, and the Meshy skull's base colour and tangent-space normals
baked onto it (Cycles, selected to active, SIZE px). The collapse-decimated Meshy skull broke into shards below 300
triangles (sockets, teeth and small holes), so the far-dense pile uses this proxy instead.
Writes work/skullproxy.blend (object 'skullproxy', front -y, centred on its bounds), work/skullproxy_base.png and
work/skullproxy_normal.png. Usage: blender --background ../work/skull_tex.blend --python bake_skull_proxy.py"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

SEGMENTS, RINGS = 10, 7
SIZE = 512
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
hi = bpy.data.objects['skull']
# Bake from the 2k Meshy base colour (the 512 runtime copy is too soft for a source).
mat = hi.data.materials[0]
tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.colorspace_settings.name == 'sRGB')
tex.image = bpy.data.images.load(os.path.join(blib.HERE, 'meshy', 'skull_retexture_v1',
                                              'texture_urls_0_base_color.png'))
co = [hi.matrix_world @ v.co for v in hi.data.vertices]
lo = Vector([min(c[i] for c in co) for i in range(3)]); top = Vector([max(c[i] for c in co) for i in range(3)])
centre = (lo + top) / 2; half = (top - lo) / 2

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=SEGMENTS, v_segments=RINGS, radius=1.0)
for v in bm.verts:
    v.co = centre + Vector((v.co.x * half.x, v.co.y * half.y, v.co.z * half.z)) * 1.05
me = bpy.data.meshes.new('skullproxy'); bm.to_mesh(me); bm.free()
proxy = bpy.data.objects.new('skullproxy', me); scene.collection.objects.link(proxy)
wrap = proxy.modifiers.new('W', 'SHRINKWRAP'); wrap.target = hi; wrap.wrap_method = 'NEAREST_SURFACEPOINT'
wrap.offset = 0.002
smooth = proxy.modifiers.new('S', 'SMOOTH'); smooth.factor = 0.5; smooth.iterations = 2
for o in bpy.data.objects:
    o.select_set(o is proxy)
bpy.context.view_layer.objects.active = proxy
for name in ('W', 'S'):
    bpy.ops.object.modifier_apply(modifier=name)
blib.triangulate(proxy)
for p in proxy.data.polygons:
    p.use_smooth = True
blib.smart_uv(proxy, angle=math.radians(70), margin=0.02)

out = bpy.data.materials.new('Bone'); out.use_nodes = True
proxy.data.materials.append(out)
target = out.node_tree.nodes.new('ShaderNodeTexImage')
out.node_tree.nodes.active = target
for o in bpy.data.objects:
    o.select_set(o in (proxy, hi))
bpy.context.view_layer.objects.active = proxy
bake = scene.render.bake
bake.use_selected_to_active = True
bake.cage_extrusion = 0.02
bake.max_ray_distance = 0.06
bake.margin = 6
for kind, path in (('DIFFUSE', 'skullproxy_base.png'), ('NORMAL', 'skullproxy_normal.png')):
    image = bpy.data.images.new(kind, SIZE, SIZE)
    if kind == 'NORMAL':
        image.colorspace_settings.name = 'Non-Color'
    target.image = image
    if kind == 'DIFFUSE':
        bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
    else:
        bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type='NORMAL')
    image.filepath_raw = os.path.join(blib.WORK, path); image.file_format = 'PNG'; image.save()
    print('BAKED', kind, path)
proxy.data.materials.clear()
proxy.data.transform(Matrix.Translation(-centre))
for o in list(bpy.data.objects):
    if o is not proxy:
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'skullproxy.blend'))
print('PROXY', 'tris', len(proxy.data.polygons))
