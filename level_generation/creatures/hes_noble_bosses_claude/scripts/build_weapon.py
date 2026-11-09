"""Build a weapon object from weapon_relief.py output: mesh, UVs, the painting as base colour, glow faces on their
own material, decimated to a triangle budget. Saves <out>.blend and <out>.glb (no rig; the mesh origin is the
painting's bottom centre, y along the weapon, x across, z thickness).

Usage (Blender): build_weapon.py <relief.npz> <painting.png> <out_stem> <name> [target_tris] [glow_rgb]"""
import bpy, bmesh, sys, os
import numpy as np

args = sys.argv[sys.argv.index('--') + 1:]
npz, painting, out, name = args[:4]
target = int(args[4]) if len(args) > 4 else 1500
glow_rgb = [float(x) for x in args[5].split(',')] if len(args) > 5 else [1.0, 0.45, 0.12]
d = np.load(npz)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new(name)
verts, faces, uvs, glow = d['verts'], d['faces'], d['uvs'], d['glow']
me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
me.update()
uvl = me.uv_layers.new(name='UVMap')
loop_v = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', loop_v)
uvl.data.foreach_set('uv', uvs[loop_v].ravel())
img = bpy.data.images.load(os.path.abspath(painting)); img.name = name + '_paint'; img.pack()


def material(mname, emissive):
    m = bpy.data.materials.new(mname); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Metallic'].default_value = 0.0
    if emissive:
        bsdf.inputs['Emission Color'].default_value = (*glow_rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


me.materials.append(material(name + '_Weapon', False))
me.materials.append(material(name + '_Glow', True))
me.polygons.foreach_set('material_index', glow.astype(np.int32))
obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
# Weld the knife-edge seam, then decimate keeping the material borders.
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(me); bm.free()
tris = len(me.polygons)
if tris > target:
    mod = obj.modifiers.new('dec', 'DECIMATE'); mod.ratio = target / tris
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.shade_smooth()
try:
    bpy.ops.object.shade_auto_smooth(angle=0.75)
except Exception:
    pass
print('WEAPON', name, len(me.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=out + '.blend')
bpy.ops.export_scene.gltf(filepath=out + '.glb', export_format='GLB', use_selection=True)
