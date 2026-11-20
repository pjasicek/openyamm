"""Review renders of a prop's exported (unlinked) GLB: LOD0 from the front (sprite-like, low elevation) and three-
quarter, and every LOD from the same view. Flipbook materials show their first frame, emissive like the engine's
unlit fire; the glTF importer multiplies base colours by COLOR_0, as the engine does. Then sheet.py combines them
with the native sprite. Usage: blender --background --python review.py -- <prop> <export.glb> <yaw_deg>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

prop, glb, yaw = sys.argv[sys.argv.index('--') + 1:]
yaw = int(yaw)
out = os.path.join(pl.PROPS, 'review', prop); os.makedirs(out, exist_ok=True)
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
for m in bpy.data.materials:
    flip = m.get('openyamm_flipbook')
    if flip is not None and m.node_tree:
        nt = m.node_tree
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)   # first frame (top-left, Blender v up)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')        # unlit in the engine: glow here too
        base = bsdf.inputs['Base Color'].links            # the texture times COLOR_0 when the importer wired it
        nt.links.new(base[0].from_socket if base else tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
pl.setup_render((512, 512))
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((yaw, 6), (yaw + 40, 24), (yaw + 180, 10)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 40, 20),))
print('REVIEW', out, [o.name for o in objects])
