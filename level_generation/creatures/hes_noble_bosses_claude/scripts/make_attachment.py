"""Weapon attachment GLB in the boss's Weapon_R joint frame (the Overseer's CollarRod grip frame, glTF axes): the
weapon's length along +Z with the grip at the origin, the blade plane in Y, thickness in X. Adds a wrapped grip
sleeve (the accepted fist is fitted to a 3.2 cm handle) textured from the painting's grip strip.

Usage (Blender): make_attachment.py <relief.npz> <painting.png> <out.glb> <name> --grip Y --sleeve Y0,Y1
                 [--radius 0.029] [--tris 1500] [--flip-y]
Writes <out.glb> (export_yup off: Blender coordinates = glTF coordinates) and <out>.blend."""
import bpy, bmesh, sys, os, math, argparse
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('npz'); ap.add_argument('painting'); ap.add_argument('out'); ap.add_argument('name')
ap.add_argument('--grip', type=float, required=True)
ap.add_argument('--sleeve', required=True)
ap.add_argument('--radius', type=float, default=0.029)
ap.add_argument('--tris', type=int, default=1500)
ap.add_argument('--flip-y', action='store_true')
a = ap.parse_args(argv)
d = np.load(a.npz)
verts, faces, uvs, glow = d['verts'].astype(float), d['faces'], d['uvs'], d['glow']
px, (Wimg, Himg), bottom, cx = float(d['px']), d['size'], float(d['bottom']), float(d['cx'])
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(os.path.abspath(a.painting)); img.name = a.name + '_paint'; img.pack()


def material(mname, emissive):
    m = bpy.data.materials.new(mname); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.5; bsdf.inputs['Metallic'].default_value = 0.0
    return m


# ---------------------------------------------------------------- relief + sleeve in weapon coordinates
y0, y1 = [float(v) for v in a.sleeve.split(',')]
seg, rings = 16, 6
sv, sf, suv = [], [], []
xc = float(verts[np.abs(verts[:, 1] - (y0 + y1) / 2) < 0.02][:, 0].mean())
for r in range(rings + 1):
    y = y0 + (y1 - y0) * r / rings
    for s in range(seg + 1):
        ang = 2 * math.pi * s / seg
        sv.append((xc + a.radius * math.cos(ang), y, a.radius * math.sin(ang)))
        prow = bottom - y / px
        suv.append((0.5 + 0.05 * (s / seg - 0.5), 1 - prow / Himg))
for r in range(rings):
    for s in range(seg):
        i0 = r * (seg + 1) + s
        sf.append((i0, i0 + 1, i0 + seg + 2)); sf.append((i0, i0 + seg + 2, i0 + seg + 1))
# caps: two fans
for yy, flip in ((y0, True), (y1, False)):
    c = len(sv); sv.append((xc, yy, 0.0)); suv.append((0.5, 1 - (bottom - yy / px) / Himg))
    base = 0 if yy == y0 else rings * (seg + 1)
    for s in range(seg):
        f = (c, base + s + 1, base + s) if flip else (c, base + s, base + s + 1)
        sf.append(f)
nv = len(verts)
allv = np.concatenate([verts, np.array(sv)])
allf = np.concatenate([faces, np.array(sf) + nv])
alluv = np.concatenate([uvs, np.array(suv)])
mat_idx = np.concatenate([glow.astype(int), np.zeros(len(sf), int)])
# weapon (x across, y along, z thick) -> joint frame: X = z, Y = x, Z = y - grip
J = np.stack([allv[:, 2], allv[:, 0] * (-1 if a.flip_y else 1), allv[:, 1] - a.grip], 1)
me = bpy.data.meshes.new(a.name)
me.from_pydata([tuple(v) for v in J], [], [tuple(f) for f in allf]); me.update()
if a.flip_y:
    me.flip_normals()
uvl = me.uv_layers.new(name='UVMap')
lv = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', lv)
uvl.data.foreach_set('uv', alluv[lv].ravel())
me.materials.append(material(a.name + '_Weapon', False)); me.materials.append(material(a.name + '_Glow', True))
me.polygons.foreach_set('material_index', mat_idx.astype(np.int32))
obj = bpy.data.objects.new(a.name, me); bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
n0 = len(me.polygons)
if n0 > a.tris:
    mod = obj.modifiers.new('dec', 'DECIMATE'); mod.ratio = a.tris / n0; mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.shade_smooth()
try:
    bpy.ops.object.shade_auto_smooth(angle=0.75)
except Exception:
    pass
print('ATTACHMENT', a.name, len(me.polygons), 'tris; z range', J[:, 2].min().round(3), J[:, 2].max().round(3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(a.out)[0] + '.blend')
bpy.ops.export_scene.gltf(filepath=a.out, export_format='GLB', use_selection=True, export_yup=False,
                          export_animations=False)
