"""v2 props from Meshy (user review of v1: the helmet must be its own model; the shield is a HEATER shield with a gold
emblem, not round): meshy/helmet_geometry_v1 and meshy/shield_geometry_v1 (Smart Topology + texture of the gated HD
prop images references_hd/v2/helmet.png, shield.png) into work/props.blend as 'HelmetMesh' and 'ShieldMesh'
(replacing the v1 local dish), each with its Meshy material and maps (copied to textures/props/<x>_*.png).
Both returns face -Y with +Z up.
- Shield prop space (export_runtime.py frame): origin on the forearm axis at the strap, +Y along the forearm toward
  the hand (= toward the heater's point: the native carries it point down on a hanging arm), +Z out of the face
  (emblem), X completes the frame. Height SHIELD_H; the strap at STRAP_T of the height from the top; the origin sits
  where the shield's back stays >= CLEAR m from the forearm axis over FOREARM_SPAN along it (the v1 dish let the
  forearm poke through its rim).
- Helmet: kept in its own space (scaled and placed on the head by helmet_fit.py), only centred on its opening.
Decimated to HELMET_TRIS / SHIELD_TRIS with sharp edges protected. Args: none"""
import bpy, bmesh, os, json, math, shutil
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
E = lambda k, d: float(os.environ.get(k, d))
SHIELD_H, STRAP_T, CLEAR, SPAN = E('SHIELD_H', 0.72), E('STRAP_T', 0.42), E('CLEAR', 0.06), E('FOREARM_SPAN', 0.16)
TRIS = {'helmet': int(E('HELMET_TRIS', 1400)), 'shield': int(E('SHIELD_TRIS', 900))}
bpy.ops.wm.open_mainfile(filepath=R('work', 'props.blend'))


def load(job, name):
    for k in ('base_color', 'normal', 'metallic', 'roughness'):
        shutil.copyfile(R('meshy', job, f'texture_urls_0_{k}.png'), R('textures', 'props', f'{name}_{k}.png'))
    old = bpy.data.objects.get(name.capitalize() + 'Mesh')
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=R('meshy', job, 'model_urls_glb.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    ob = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
    for o in new:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    t0 = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if t0 > TRIS[name]:
        bm = bmesh.new(); bm.from_mesh(ob.data)
        keep = {v.index for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(70) for v in e.verts}
        bm.free()
        vg = ob.vertex_groups.new(name='_keep'); vg.add(sorted(keep), 1.0, 'REPLACE')
        dm = ob.modifiers.new('dec', 'DECIMATE'); dm.decimate_type = 'COLLAPSE'; dm.ratio = TRIS[name] / t0
        dm.vertex_group = '_keep'; dm.invert_vertex_group = True
        bpy.ops.object.modifier_apply(modifier='dec')
        ob.vertex_groups.remove(ob.vertex_groups['_keep'])
    ob.name = ob.data.name = name.capitalize() + 'Mesh'
    for m in ob.data.materials:
        m.name = name.capitalize()
    return ob, t0


# ---------------------------------------------------------------- shield
sh, t0 = load('shield_geometry_v1', 'shield')
co = np.array([tuple(v.co) for v in sh.data.vertices])
k = SHIELD_H / np.ptp(co[:, 2])
co = (co - [(co[:, 0].max() + co[:, 0].min()) / 2, 0, co[:, 2].max()]) * k     # x centred, top at z = 0
# prop axes: X = -x, Y = -z (down toward the point), Z = -y (out of the face, the return faces -Y)
P = np.column_stack([-co[:, 0], -co[:, 2], -co[:, 1]])
P[:, 1] -= STRAP_T * SHIELD_H
# back surface over the forearm span: the most-negative Z near the axis (|X| < 5 cm, |Y| < SPAN)
band = (np.abs(P[:, 0]) < 0.05) & (np.abs(P[:, 1]) < SPAN)
back = float(P[band, 2].min())
P[:, 2] += CLEAR - back
for v, p in zip(sh.data.vertices, P):
    v.co = tuple(p)
sh.data.update()
# check by ray: the back along the forearm axis
bm = bmesh.new(); bm.from_mesh(sh.data); tree = BVHTree.FromBMesh(bm); bm.free()
gap = []
for y in np.linspace(-SPAN, SPAN, 9):
    hit = tree.ray_cast(Vector((0, y, -0.5)), Vector((0, 0, 1)))
    gap.append(round(hit[0].z, 3) if hit[0] else None)
print('SHIELD tris', t0, '->', sum(len(p.vertices) - 2 for p in sh.data.polygons), 'height', round(float(np.ptp(P[:, 1])), 3),
      'width', round(float(np.ptp(P[:, 0])), 3), 'back z along the forearm', gap)
# ---------------------------------------------------------------- helmet
hm, t0 = load('helmet_geometry_v1', 'helmet')
co = np.array([tuple(v.co) for v in hm.data.vertices])
print('HELMET tris', t0, '->', sum(len(p.vertices) - 2 for p in hm.data.polygons), 'size', np.round(np.ptp(co, axis=0), 3))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
