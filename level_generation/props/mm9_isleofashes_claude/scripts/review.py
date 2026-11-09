"""Blender: review renders of each finished GLB (work/mm9_deco_<prop>.glb, else work/<prop>_export.glb), imported as
the engine will draw it (back faces culled on single-sided materials): LOD0 from the front, three-quarter, side,
behind-above and below, and each LOD three-quarter. Writes review/<prop>/*.png.
Usage: blender --background --python review.py -- [prop ...]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

VIEWS = (('front', 0, 8), ('threequarter', 35, 22), ('side', 90, 8), ('back', 200, 35), ('below', 30, -35))


def frame_fire():
    for m in bpy.data.materials:
        if m.node_tree and m.name.startswith('Fire') and not any(n.type == 'MAPPING' for n in m.node_tree.nodes):
            # the flame flipbook's first frame (the engine steps through the 16 x 4 frames)
            nt = m.node_tree
            tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
            coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
            mapping.inputs['Scale'].default_value = (1 / 16, 1 / 4, 1)
            mapping.inputs['Location'].default_value = (0, 0.75, 0)
            nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
            nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
props = args or sorted(f[:-11] for f in os.listdir(blib.WORK) if f.endswith('_export.glb'))
for prop in props:
    path = os.path.join(blib.WORK, f'mm9_deco_{prop}.glb')
    if not os.path.exists(path):
        path = os.path.join(blib.WORK, f'{prop}_export.glb')
    blib.reset()
    blib.setup_render((400, 400))
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    frame_fire()
    out = os.path.join(blib.HERE, 'review', prop)
    os.makedirs(out, exist_ok=True)
    base = [o for o in meshes if '_LOD' not in o.name]
    for name, yaw, el in VIEWS:
        blib.render(base, os.path.join(out, f'lod0_{name}.png'), yaw, el)
    # the finished GLB lists its LOD meshes in extras only: render them from the unlinked export
    for o in meshes:
        o.hide_render = True
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(blib.WORK, f'{prop}_export.glb'))
    frame_fire()
    lods = sorted([o for o in bpy.data.objects if o not in before and '_LOD' in o.name], key=lambda o: o.name)
    for i, o in enumerate(lods, 1):
        blib.render([o], os.path.join(out, f'lod{i}_threequarter.png'), 35, 22)
    print('REVIEWED', prop, [o.name for o in meshes])
