"""Inner cloak shell follows the outer shell: every inner-side vertex (cloak_sides.py) sits at least
MIN_THICK inside its nearest outer-face point at rest (moved along that face's normal) and takes that point's weights
(barycentric blend of the outer face's vertex weights, top 4, normalised), so the two surfaces of the cloth move as
one and the inside cannot pass through the outside (shell_cross.py). cloak_rig.py weighted each surface by its own
distance to the arm and its own smoothing (the inner left side panel crossed the outer by 10-17 mm in every clip),
and Smart Topology left the shells 3-7 mm apart near the hem, where a fold crossed them in Walking and Death (spots
once the inside was shaded darker, prepare_textures.py). Runs on the given blend in place, after cloak_sim.
Args: blend."""
import bpy, sys, os, json
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend = sys.argv[sys.argv.index('--') + 1]
path = os.path.join(common.WORK, blend)
bpy.ops.wm.open_mainfile(filepath=path)
arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data
REG = json.loads(bpy.context.scene['cle_uv_regions'])
ureg = [0] * len(me.polygons); me.attributes['uv_region'].data.foreach_get('value', ureg)
CLOAK = {'CloakB', 'CloakL', 'CloakR', 'Mantle', 'CloakBi', 'CloakLi', 'CloakRi', 'Mantlei'}
SIDE_IN = set(json.loads(open(os.path.join(common.WORK, 'cloak_sides.json')).read())['inner'])   # cloak_sides.py
MIN_THICK = 0.015
me.calc_loop_triangles()
otris = [t for t in me.loop_triangles if REG[ureg[t.polygon_index]] in CLOAK and t.polygon_index not in SIDE_IN]
ovset = {v for t in otris for v in t.vertices}
iverts = sorted({v for p in me.polygons if p.index in SIDE_IN for v in p.vertices} - ovset)
R = [v.co.copy() for v in me.vertices]          # rest positions (mesh space; the mesh is not deformed at rest)
tree = BVHTree.FromPolygons(R, [tuple(t.vertices) for t in otris])
names = {g.index: g.name for g in mesh.vertex_groups}
deform = {b.name for b in arm.data.bones if b.use_deform}


def weights(v):
    return {names[g.group]: g.weight for g in me.vertices[v].groups if names[g.group] in deform and g.weight > 0}


new = {}
moved = 0
for v in iverts:
    loc, _, fi, dist = tree.find_nearest(R[v])
    if fi is None or dist > 0.05:
        continue
    a, b, c = otris[fi].vertices
    normal = (R[b] - R[a]).cross(R[c] - R[a]).normalized()
    offset = (R[v] - loc).dot(normal)
    if offset > -MIN_THICK:
        me.vertices[v].co = R[v] + normal * (-MIN_THICK - offset)
        moved += 1
    # barycentric coordinates of loc in the outer triangle
    w = barycentric_transform(loc, R[a], R[b], R[c], *[__import__('mathutils').Vector(e) for e in
                                                        ((1, 0, 0), (0, 1, 0), (0, 0, 1))])
    blend_w = {}
    for corner, share in zip((a, b, c), (max(w.x, 0), max(w.y, 0), max(w.z, 0))):
        for name, value in weights(corner).items():
            blend_w[name] = blend_w.get(name, 0.0) + share * value
    top = sorted(blend_w.items(), key=lambda item: -item[1])[:4]
    total = sum(value for _, value in top)
    if total > 0:
        new[v] = {name: value / total for name, value in top}
for v, ws in new.items():
    for g in list(me.vertices[v].groups):
        if names[g.group] in deform:
            mesh.vertex_groups[g.group].remove([v])
    for name, value in ws.items():
        mesh.vertex_groups[name].add([v], value, 'REPLACE')
print('SHELL_WEIGHTS', len(new), 'of', len(iverts), 'inner vertices,', moved, 'moved inward to', MIN_THICK, 'm')
bpy.ops.wm.save_mainfile(filepath=path)
