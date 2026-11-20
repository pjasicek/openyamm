"""Texture post-process of the retextured foreleg (TEXTURE_QUALITY_PASS): Meshy's 4K maps downsampled once to 2K,
nearest-texel gutter fill last, then a textured foreleg GLB for build_forelegs.py.

blender -b --python texture_pass.py -- extract <retextured.glb> <maps_dir>
python3 texture_pass.py resize <maps_dir>            (system Python: PIL; then gutter_fill.py on the 2K maps)
blender -b --python texture_pass.py -- rebuild <retextured.glb> <maps_dir> <out.glb>
"""
import sys
from pathlib import Path

ROLES = {'Base Color': 'basecolor', 'Normal': 'normal', 'Metallic': 'orm', 'Roughness': 'orm'}


def blender_main(argv):
    import bpy
    mode, source, maps = argv[0], argv[1], Path(argv[2])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    material = obj.data.materials[0]
    nodes = material.node_tree.nodes
    images = {}
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            # Follow the link to the principled input (through a normal map or separate node).
            role = None
            stack = [link.to_node for link in node.outputs[0].links]
            sockets = [link.to_socket.name for link in node.outputs[0].links]
            for target, socket in zip(stack, sockets):
                if target.type == 'BSDF_PRINCIPLED':
                    role = ROLES.get(socket)
                elif target.type == 'NORMAL_MAP':
                    role = 'normal'
                elif target.type in ('SEPARATE_COLOR', 'SEPARATE_RGB'):
                    role = 'orm'
            images[role or node.image.name] = node
    print('IMAGES', {k: (v.image.name, tuple(v.image.size)) for k, v in images.items()})
    if mode == 'extract':
        maps.mkdir(parents=True, exist_ok=True)
        for role, node in images.items():
            node.image.filepath_raw = str(maps / f'{role}_4k.png')
            node.image.file_format = 'PNG'
            node.image.save()
        return
    out = argv[3]
    for role, node in images.items():
        path = maps / f'{role}_2k.png'
        image = bpy.data.images.load(str(path))
        image.colorspace_settings.name = node.image.colorspace_settings.name
        node.image = image
        image.pack()
    for o in list(bpy.context.scene.objects):
        if o is not obj:
            bpy.data.objects.remove(o)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
    print('REBUILT', out)


def resize_main(maps):
    from PIL import Image
    for path in sorted(Path(maps).glob('*_4k.png')):
        image = Image.open(path)
        image.resize((2048, 2048), Image.LANCZOS).save(str(path).replace('_4k.png', '_2k.png'))
        print('RESIZED', path.name, image.size, '->', (2048, 2048))


if '--' in sys.argv:
    blender_main(sys.argv[sys.argv.index('--') + 1:])
elif len(sys.argv) > 2 and sys.argv[1] == 'resize':
    resize_main(sys.argv[2])
