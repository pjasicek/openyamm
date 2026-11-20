"""Physical sides of the cloak shell -> work/cloak_sides.json {'inner': [polygon indices]}. uv_cle.py labelled each
cloak face outer or inner (CloakB/Bi ...) by its own normal against the radial direction, unsmoothed: 131 faces near
the hem and the front edges carry the other side's label (inner-labelled patches on the outer back, outer-labelled on
the inside), which showed as sharp triangles once the inside was shaded darker. Here each side is a fold component:
faces joined across edges whose normals agree within FOLD (the rim turns the normal over in one or two faces); a
component takes its area-majority label when that majority is at least PURE, otherwise (a smooth turn such as the
mantle's rim) each face votes with half its label and half whether its normal faces the nearest body surface.
Small components (< SMALL faces) then follow their neighbours twice. Consumers: prepare_textures.py (inner shading),
shell_weights.py and shell_cross.py. Runs on the rest mesh before shell_weights moves it. Args: blend."""
import bpy, bmesh, sys, os, json
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
me = bpy.data.objects['Cleric'].data
REG = json.loads(bpy.context.scene['cle_uv_regions'])
OUTER = {'CloakB', 'CloakL', 'CloakR', 'Mantle'}
INNER = {'CloakBi', 'CloakLi', 'CloakRi', 'Mantlei'}
FOLD, PURE, SMALL = 0.85, 0.8, 50

bm = bmesh.new(); bm.from_mesh(me)
region = bm.faces.layers.int['uv_region']
cloak = [f for f in bm.faces if REG[f[region]] in OUTER | INNER]
cset = set(cloak)
labelled = {f: REG[f[region]] in INNER for f in cloak}
body = [f for f in bm.faces if f not in cset]
btree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(v.index for v in f.verts) for f in body])

comp, comps = {}, []
for f in cloak:
    if f in comp:
        continue
    comps.append([]); stack = [f]; comp[f] = len(comps) - 1
    while stack:
        g = stack.pop(); comps[-1].append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h in cset and h not in comp and h.normal.dot(g.normal) > FOLD:
                    comp[h] = comp[g]; stack.append(h)
inner, mixed = {}, []
for faces in comps:
    share = sum(f.calc_area() for f in faces if labelled[f]) / sum(f.calc_area() for f in faces)
    if share >= PURE or share <= 1 - PURE:
        inner.update({f: share > 0.5 for f in faces})
        continue
    mixed.append(len(faces))
    for f in faces:
        c = f.calc_center_median()
        facing = 0.5 + 0.5 * f.normal.dot((btree.find_nearest(c)[0] - c).normalized())
        inner[f] = 0.5 * facing + 0.5 * labelled[f] > 0.5
for _ in range(2):
    vote = dict(inner)
    for f in cloak:
        if len(comps[comp[f]]) >= SMALL:
            continue
        nb = [g for e in f.edges for g in e.link_faces if g is not f and g in cset]
        vote[f] = (sum(inner[g] for g in nb) + inner[f]) * 2 > len(nb) + 1
    inner = vote
faces = sorted(f.index for f in cloak if inner[f])
relabelled = sum(inner[f] != labelled[f] for f in cloak)
(open(os.path.join(common.WORK, 'cloak_sides.json'), 'w')
 .write(json.dumps({'inner': faces, 'relabelled': relabelled})))
print('CLOAK_SIDES', json.dumps({'cloak': len(cloak), 'inner': len(faces), 'relabelled': relabelled,
                                 'components': len(comps), 'mixed': mixed}))
