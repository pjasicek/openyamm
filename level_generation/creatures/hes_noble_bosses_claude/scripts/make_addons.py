"""Procedural signature add-ons of the Noble bosses, rigid on their bones (rest pose, world = body space), saved into
work/<boss>/shell_tex.blend as AddOn_* objects (assemble.py joins them into the Noble mesh):
  coil_keeper: two glass coil capsules on the upper back between the wing roots (gold windings, ivory caps);
  hierarch:    a crown of fused ivory bone spikes round the skull between the horns; five spinal cables hanging
               down the back with gold couplings and glowing plugs;
  conductor:   three ribbed cables from gold sockets on the back of the left forearm with glowing plugs, and a
               glowing throat node.
Opaque parts sample swatches of textures/addon_palette.png (material <Boss>_AddOn); glowing parts use
<Boss>_AddGlow (emission set later by claude_shared/emission.py). Usage (Blender): make_addons.py <boss>"""
import bpy, bmesh, sys, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix

boss = sys.argv[sys.argv.index('--') + 1:][0]
P = Path(__file__).resolve().parents[1]
W = P / 'work' / boss
bpy.ops.wm.open_mainfile(filepath=str(W / 'shell_tex.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']
body = bpy.data.objects[f'Body_{boss}']
for o in [o for o in sc.objects if o.name.startswith('AddOn_')]:
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- palette (swatch centres in UV)
SW = {'gold': (0, 0), 'ivory': (1, 0), 'resin': (2, 0), 'cable': (3, 0), 'darkgold': (0, 1), 'glass': (1, 1)}
COL = {'gold': (0.86, 0.66, 0.30), 'ivory': (0.90, 0.85, 0.72), 'resin': (0.16, 0.08, 0.17),
       'cable': (0.10, 0.07, 0.10), 'darkgold': (0.55, 0.38, 0.15), 'glass': (0.55, 0.45, 0.70)}
pal = P / 'textures/addon_palette.png'
if not pal.exists():
    img = bpy.data.images.new('addon_palette', 64, 64)
    px = np.zeros((64, 64, 4), np.float32); px[..., 3] = 1
    for name, (cx, cy) in SW.items():
        c = COL[name]
        # sRGB-ish values written as linear floats of a byte image
        px[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16, :3] = c
    img.pixels.foreach_set(px.ravel()); img.filepath_raw = str(pal); img.file_format = 'PNG'; img.save()


def uv_of(name):
    cx, cy = SW[name]
    return ((cx + 0.5) * 16 / 64, (cy + 0.5) * 16 / 64)


def mat(name, glow_rgb=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(pal), check_existing=True)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Metallic'].default_value = 0.0
    if glow_rgb:
        b.inputs['Emission Color'].default_value = (*glow_rgb, 1); b.inputs['Emission Strength'].default_value = 2.0
    return m


B = boss.title().replace('_', '')
M_OPQ = mat(f'{B}_AddOn')


class Part:
    def __init__(self):
        self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap'); self.mats = []

    def face(self, verts, swatch, glow=False):
        f = self.bm.faces.new(verts)
        for l in f.loops:
            l[self.uv].uv = uv_of(swatch)
        f.material_index = 1 if glow else 0
        return f

    def tube(self, pts, radii, swatch, sides=8, glow=False, cap=True):
        pts = [Vector(p) for p in pts]; rings = []
        prev_n = None
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            n = prev_n if prev_n is not None else d.orthogonal().normalized()
            n = (n - d * n.dot(d)).normalized(); prev_n = n; bnorm = d.cross(n)
            r = radii[i] if hasattr(radii, '__len__') else radii
            rings.append([self.bm.verts.new(p + (n * math.cos(a) + bnorm * math.sin(a)) * r)
                          for a in (2 * math.pi * k / sides for k in range(sides))])
        for a, b in zip(rings, rings[1:]):
            for k in range(sides):
                self.face([a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]], swatch, glow)
        if cap:
            self.face(list(reversed(rings[0])), swatch, glow); self.face(rings[-1], swatch, glow)

    def sphere(self, c, r, swatch, glow=False, seg=8, rings=5):
        c = Vector(c)
        vs = [[self.bm.verts.new(c + Vector((math.sin(math.pi * i / rings) * math.cos(2 * math.pi * k / seg),
                                             math.sin(math.pi * i / rings) * math.sin(2 * math.pi * k / seg),
                                             math.cos(math.pi * i / rings))) * r) for k in range(seg)]
              for i in range(1, rings)]
        top = self.bm.verts.new(c + Vector((0, 0, r))); bot = self.bm.verts.new(c - Vector((0, 0, r)))
        for k in range(seg):
            self.face([top, vs[0][k], vs[0][(k + 1) % seg]], swatch, glow)
            self.face([bot, vs[-1][(k + 1) % seg], vs[-1][k]], swatch, glow)
        for a, b in zip(vs, vs[1:]):
            for k in range(seg):
                self.face([a[k], b[k], b[(k + 1) % seg], a[(k + 1) % seg]], swatch, glow)

    def finish(self, name, bone, glow_mat=None, weights=None):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        me.materials.append(M_OPQ)
        if glow_mat:
            me.materials.append(glow_mat)
        o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
        if weights is None:
            g = o.vertex_groups.new(name=bone); g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
        else:
            for v in me.vertices:
                for bn, w in weights(Vector(v.co)).items():
                    g = o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn)
                    g.add([v.index], w, 'REPLACE')
        print('ADDON', name, len(me.polygons), 'tris')
        return o


# ---------------------------------------------------------------- body landmarks
BV = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
gid = {g.name: g.index for g in body.vertex_groups}


def weight_of(names):
    idx = [gid[n] for n in names if n in gid]
    w = np.zeros(len(BV))
    for v in body.data.vertices:
        w[v.index] = sum(g.weight for g in v.groups if g.group in idx)
    return w


def bone_head(n):
    return Vector(rig.matrix_world @ rig.data.bones[n].head_local)


head_w = weight_of(['B_Head'])
headv = BV[head_w > 0.8]
print('HEAD box', headv.min(0).round(3), headv.max(0).round(3))

if boss == 'coil_keeper':
    glow = mat(f'{B}_AddGlow', (0.62, 0.3, 1.0))
    # back surface behind the upper spine
    back = BV[(np.abs(BV[:, 0]) < 0.05) & (BV[:, 2] > 1.1) & (BV[:, 2] < 1.25)]
    yb = float(back[:, 1].max())
    for side in (-1, 1):
        pt = Part()
        x = side * 0.05; y = yb + 0.045; z0, z1 = 1.10, 1.43
        tilt = Vector((side * 0.06, 0.03, 1)).normalized()
        base = Vector((x, y, z0))
        L = z1 - z0

        def at(t):
            return base + tilt * (L * t)
        # glass core
        pt.tube([at(0.12), at(0.88)], 0.026, 'glass', sides=8, glow=True)
        # gold windings
        for t in np.linspace(0.2, 0.8, 5):
            ring = [at(t) + (Vector((math.cos(a), math.sin(a), 0)) * 0.031) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
            ring.append(ring[0])
            pt.tube(ring, 0.006, 'gold', sides=4, cap=False)
        # ivory caps and gold collars
        pt.tube([at(0.0), at(0.06), at(0.13)], [0.024, 0.036, 0.034], 'ivory', sides=8)
        pt.tube([at(0.87), at(0.94), at(1.0), at(1.08)], [0.034, 0.036, 0.024, 0.006], 'ivory', sides=8)
        pt.tube([at(0.10), at(0.15)], 0.038, 'gold', sides=8)
        pt.tube([at(0.85), at(0.90)], 0.038, 'gold', sides=8)
        # resin cable from the base into the spine plates
        pt.tube([at(0.03), base + Vector((-side * 0.02, -0.03, -0.05)), Vector((x * 0.4, yb - 0.005, z0 - 0.09))],
                0.012, 'cable', sides=6)
        pt.finish(f'AddOn_coil_{"L" if side > 0 else "R"}', 'B_Spine2', glow)

elif boss == 'conductor':
    glow = mat(f'{B}_AddGlow', (0.8, 0.68, 1.0))
    fa0, fa1 = bone_head('B_L_Forearm'), bone_head('B_L_Hand')
    fw = weight_of(['B_L_Forearm', 'B_L_ForearmTwist'])
    arm = BV[fw > 0.6]
    pt = Part()
    for k, t in enumerate((0.25, 0.45, 0.65)):
        c = fa0.lerp(fa1, t)
        near = arm[np.linalg.norm(arm - np.array(c), axis=1) < 0.06]
        # the back (outer) side of the forearm: away from the body's mid-line and to the back
        out = Vector((1.0, 0.6, 0)).normalized()
        surf = max((Vector(p) for p in near), key=lambda p: (p - c).dot(out)) if len(near) else c + out * 0.04
        s0 = surf + out * 0.004
        s1 = s0 + out * 0.03 + Vector((0, 0.01, -0.01))
        pt.tube([s0 - out * 0.01, s0 + out * 0.012], 0.016, 'gold', sides=8)
        hang = 0.14 + 0.03 * k
        pts = [s0 + out * 0.01, s1, s1 + Vector((0.01, 0.02, -hang * 0.5)), s1 + Vector((0.0, 0.03, -hang))]
        pt.tube(pts, 0.009, 'cable', sides=6)
        end = pts[-1]
        pt.tube([end + Vector((0, 0, 0.012)), end, end + Vector((0, 0, -0.03))], [0.013, 0.014, 0.012], 'gold', sides=8)
        pt.sphere(end + Vector((0, 0, -0.034)), 0.008, 'glass', glow=True, seg=6, rings=4)
    pt.finish('AddOn_cables', 'B_L_Forearm', glow)
    # throat node
    # the front of the throat, below the jaw: the body's front surface on the mid-line at the gorget's height
    sh = bpy.data.objects['Shell']
    SVs = np.array([tuple(sh.matrix_world @ v.co) for v in sh.data.vertices])
    band = SVs[(np.abs(SVs[:, 0]) < 0.03) & (SVs[:, 2] > 1.07) & (SVs[:, 2] < 1.13)]
    front = Vector(band[band[:, 1].argmin()]) + Vector((0, 0.004, 0.01))
    pt = Part()
    pt.sphere(front + Vector((0, -0.016, -0.01)), 0.016, 'glass', glow=True, seg=10, rings=6)
    pt.tube([front + Vector((0, -0.002, -0.01)), front + Vector((0, -0.012, -0.01))], 0.022, 'gold', sides=10)
    pt.finish('AddOn_throat', 'B_Neck', glow)

elif boss == 'hierarch':
    glow = mat(f'{B}_AddGlow', (1.0, 0.42, 0.1))
    # crown: fused bone spikes round the skull top, between and around the horns
    lo, hi = headv.min(0), headv.max(0)
    cx, cy = float((lo[0] + hi[0]) / 2), float(np.median(headv[:, 1]))
    top = headv[headv[:, 2] > hi[2] - 0.05]
    zc = float(np.percentile(headv[:, 2], 92))
    pt = Part()
    rng = np.random.default_rng(7)
    ring = []
    n = 11
    for k in range(n):
        a = math.pi * (0.15 + 1.7 * k / (n - 1)) + math.pi / 2    # an arc round the back and sides, open in front
        rx, ry = 0.055, 0.06
        p = Vector((cx + rx * math.cos(a), cy + 0.01 + ry * math.sin(a), zc))
        ring.append(p)
        length = 0.07 + 0.08 * (1 - abs(math.cos(a - math.pi * 1.5))) + rng.uniform(0, 0.03)
        outward = Vector((math.cos(a), math.sin(a), 0)) * 0.35
        d = (Vector((0, 0.15, 1)) + outward).normalized()
        bend = Vector((0, 0.04, 0))
        pts = [p - d * 0.01, p + d * length * 0.35, p + d * length * 0.7 + bend * 0.5, p + d * length + bend]
        pt.tube(pts, [0.016, 0.012, 0.007, 0.0015], 'ivory', sides=6)
    ring.append(ring[0] * 0 + ring[-1])
    pt.tube(ring[:-1], 0.014, 'ivory', sides=6)                         # the fused band
    pt.tube([r + Vector((0, 0, -0.012)) for r in ring[:-1]], 0.009, 'gold', sides=5)
    pt.finish('AddOn_crown', 'B_Head')
    # spinal cables: from between the shoulder blades down the back to the back of the knees
    back = BV[(np.abs(BV[:, 0]) < 0.06) & (BV[:, 2] > 1.05) & (BV[:, 2] < 1.2)]
    yb = float(back[:, 1].max())
    buttock = float(BV[(np.abs(BV[:, 0]) < 0.12) & (BV[:, 2] > 0.75) & (BV[:, 2] < 0.9)][:, 1].max())
    pelvis_z, spine2_z = bone_head('B_Pelvis').z, bone_head('B_Spine2').z

    def wts(p):
        t = max(0.0, min(1.0, (spine2_z - p.z) / (spine2_z - pelvis_z)))
        return {'B_Spine2': 1 - t, 'B_Pelvis': t} if t < 1 else {'B_Pelvis': 1.0}
    pt = Part()
    for k, x in enumerate((-0.06, -0.03, 0.0, 0.03, 0.06)):
        y0 = yb + 0.012; z0 = 1.17 - abs(x) * 0.6
        length = 0.62 + 0.05 * (k % 2)
        yb2 = max(buttock + 0.05, y0 + 0.03)
        pts = [Vector((x * 0.6, y0 - 0.02, z0)), Vector((x * 0.8, y0 + 0.02, z0 - 0.06)),
               Vector((x * 1.1, yb2, z0 - 0.35)), Vector((x * 1.25, yb2 + 0.01, z0 - length))]
        pt.tube(pts, [0.014, 0.017, 0.017, 0.016], 'cable', sides=7)
        for t in (0.0, 1.0):
            c = pts[0] if t == 0 else pts[-1]
            d = (pts[1] - pts[0]).normalized() if t == 0 else (pts[-1] - pts[-2]).normalized()
            pt.tube([c - d * 0.01, c + d * 0.025], 0.022, 'gold', sides=8)
        end = pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.035
        pt.sphere(end, 0.012, 'glass', glow=True, seg=6, rings=4)
    pt.finish('AddOn_cables', None, glow, weights=wts)
else:
    print('no add-ons for', boss)
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'shell_tex.blend'))
