"""Import a GLB's LOD0 node (object 'Tree') and save it as a blend for dead_render.py review renders.
Usage: blender -b -P glb_to_blend.py -- in.glb out.blend"""
import sys, bpy
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
o.name = 'Tree'
if o.data.color_attributes and 'Color' not in o.data.color_attributes:
    o.data.color_attributes[0].name = 'Color'
for m in o.data.materials:
    # the importer may route base colour through mix nodes: link the base-colour image straight to the BSDF, as the
    # pipeline's own blends have it (dead_render.py multiplies it by 'Color')
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    link = bsdf.inputs['Base Color'].links
    if link and link[0].from_node.type != 'TEX_IMAGE':
        stack = [link[0].from_node]; img = None
        while stack and img is None:
            n = stack.pop()
            for i in n.inputs:
                for l in i.links:
                    if l.from_node.type == 'TEX_IMAGE':
                        img = l.from_node
                    else:
                        stack.append(l.from_node)
        if img is not None:
            nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
bpy.ops.wm.save_as_mainfile(filepath=out)
