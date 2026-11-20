"""The Custodian's materials and glow geometry on the adopted retexture mesh (work/tex.blend) -> work/build.blend.

Materials: Cust (textures/cust_basecolor 2048, cust_normal, cust_orm 1024), Cust_Glow (the eye lens and the nine
vents: a dark red-orange base under an orange-red emission, untextured; integrator review 2026-10-23: a bright amber
base lit on top of the emission read pale yellow), Cust_Lens (the sensor lens: blue-white, untextured). Their emission is set on the exported
GLB (claude_shared/emission.py), not here.
Glow geometry (the retexture painted no eye, and painted the vents only as colour):
- the eye: a lens dome in the gap between the two rings at the front (rays from the front find it), on Body; Socket_Eye goes to its apex (rig_anim.py reads work/eye.json);
- the vents: a flat disc 4 mm under each vent Meshy painted (textures/cust_glow.json, compose.py), on Body;
- the sensor lens: a small disc on the sensor box's front face, toward its left (+x) end as on the concept, on Sensor.
Args: none."""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=cc.path('work/tex.blend'))
scene = bpy.context.scene
body = bpy.data.objects['Custodian']
J = json.loads(body['joints'])
glow = json.load(open(cc.path('textures/cust_glow.json')))
co = np.array([v.co[:] for v in body.data.vertices])
fpart = np.zeros(len(body.data.polygons), int); body.data.attributes['part'].data.foreach_get('value', fpart)
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())


def image(name, colour):
    img = bpy.data.images.load(cc.path('textures', name))
    img.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return img


def material(name, base=None, colour=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    if base:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = image('cust_basecolor.png', True)
        nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
        o = nt.nodes.new('ShaderNodeTexImage'); o.image = image('cust_orm.png', False)
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(o.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        nm = nt.nodes.new('ShaderNodeTexImage'); nm.image = image('cust_normal.png', False)
        nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        bsdf.inputs['Base Color'].default_value = (*colour, 1)
        bsdf.inputs['Roughness'].default_value = 0.3
        bsdf.inputs['Metallic'].default_value = 0.0
    return m


body.data.materials.clear()
for m in (material('Cust', base=True), material('Cust_Glow', colour=(0.30, 0.05, 0.01)),
          material('Cust_Lens', colour=(0.7, 0.85, 1.0))):
    body.data.materials.append(m)

bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
mat_of, bone_of = [], []


def add_disc(centre, normal, radius, mat, bone, sides=16):
    n = Vector(normal).normalized(); a = n.orthogonal().normalized(); b = n.cross(a)
    ring = [bm.verts.new(Vector(centre) + (a * math.cos(2 * math.pi * i / sides) + b * math.sin(2 * math.pi * i / sides)) * radius)
            for i in range(sides)]
    inner = [bm.verts.new(Vector(centre) + (a * math.cos(2 * math.pi * i / 8) + b * math.sin(2 * math.pi * i / 8)) * radius * 0.45)
             for i in range(8)]
    faces = [inner[::-1]]
    for i in range(sides):
        j = (i + 1) % sides; ii, jj = (i * 8 // sides) % 8, ((i + 1) * 8 // sides) % 8
        faces.append(([ring[i], ring[j], inner[jj]] + ([inner[ii]] if ii != jj else []))[::-1])
    for fv in faces:
        f = bm.faces.new(fv)
        if f.normal.dot(n) < 0:
            f.normal_flip()
        mat_of.append(mat); bone_of.append(bone)


def add_dome(centre, forward, rx, rz, depth, mat, bone, seg=16, rings=5):
    """A lens dome: an elliptic cap (rx wide, rz tall) bulging `depth` along `forward` from its base plane."""
    f = Vector(forward).normalized(); x = Vector((1, 0, 0)); z = f.cross(x).normalized() * -1
    if z.z < 0:
        z = -z
    grid = []
    for r in range(rings + 1):
        t = r / rings                                      # 0 base ring .. 1 apex
        ang = t * math.pi / 2
        rad, h = math.cos(ang), math.sin(ang)
        row = [bm.verts.new(Vector(centre) + x * rx * rad * math.cos(2 * math.pi * i / seg)
                            + z * rz * rad * math.sin(2 * math.pi * i / seg) + f * depth * h) for i in range(seg)]
        grid.append(row)
    for r in range(rings):
        for i in range(seg):
            j = (i + 1) % seg
            q = [grid[r][i], grid[r][j], grid[r + 1][j], grid[r + 1][i]]
            if r == rings - 1:
                q = [grid[r][i], grid[r][j], grid[r + 1][j]]
            face = bm.faces.new(q)
            if face.normal.dot(f) < -0.2 and r == 0:
                face.normal_flip()
            mat_of.append(mat); bone_of.append(bone)
    apex = Vector(centre) + f * depth
    return apex


# the eye: the gap between the two rings at the front (x = 0). Rays from the front fall into it and hit the rings'
# inner faces (normals pointing back); the dome sits in that run of heights, its base 8 cm behind the rings' front (the gap
# opens into the hollow sphere), bulging 3.5 cm past it (scripts/profile.py printed the profile: gap z 1.45-1.65, rings' front y -1.15..-1.16).
prof = []
for z in np.arange(J['Body'][2] - 0.6, J['Body'][2] + 0.4, 0.0125):
    hit = bvh.ray_cast(Vector((0, -4, z)), Vector((0, 1, 0)))
    if hit[0] is not None:
        prof.append((float(z), hit[0].y, hit[1].y))
gap = [p for p in prof if p[2] > 0]
runs, cur = [], [gap[0]]
for p in gap[1:]:
    if p[0] - cur[-1][0] < 0.02:
        cur.append(p)
    else:
        runs.append(cur); cur = [p]
runs.append(cur)
run = max(runs, key=len)
z_lo, z_hi = run[0][0], run[-1][0]
ring_y = min(p[1] for p in prof if abs(p[0] - (z_lo + z_hi) / 2) < 0.4)
y_back = ring_y + 0.08                                   # the gap opens into the hollow sphere: base 8 cm deep
eye_c = Vector((0.0, y_back, (z_lo + z_hi) / 2))
depth = 0.08 + 0.035
rz = max(0.08, (z_hi - z_lo) / 2 + 0.02)
apex = add_dome(eye_c, (0, -1, 0), rz * 1.6, rz, depth, 1, 'Body')
json.dump({'eye_apex': list(apex), 'eye_base': list(eye_c)}, open(cc.path('work/eye.json'), 'w'))
print('EYE gap z', round(z_lo, 3), round(z_hi, 3), 'back y', round(y_back, 3), 'rings y', round(ring_y, 3),
      'apex', [round(c, 3) for c in apex], 'rz', round(rz, 3))

for v in glow['vents']:
    c = Vector(v['centre'])
    hit = bvh.ray_cast(Vector((c.x, c.y, -1.0)), Vector((0, 0, 1)))
    z = hit[0].z if hit[0] else c.z
    add_disc((c.x, c.y, z - 0.004), (0, 0, -1), v['radius'], 1, 'Body', sides=14)
print('VENT discs', len(glow['vents']))

sens = np.array([body.data.vertices[vi].co[:] for p in body.data.polygons if fpart[p.index] == 2 for vi in p.vertices])
x0, x1 = sens[:, 0].min(), sens[:, 0].max(); z0, z1 = sens[:, 2].min(), sens[:, 2].max()
box_z0 = np.percentile(sens[:, 2], 40)                   # the box above the post
zl = (box_z0 + z1) / 2
xl = x0 + 0.75 * (x1 - x0)
hit = bvh.ray_cast(Vector((xl, -4, zl)), Vector((0, 1, 0)))
add_disc(hit[0] + Vector((0, -0.003, 0)), (0, -1, 0), 0.32 * (z1 - box_z0), 2, 'Sensor', sides=12)
print('LENS at', [round(c, 3) for c in hit[0]], 'r', round(0.32 * (z1 - box_z0), 3))

for f in bm.faces:
    for loop in f.loops:
        loop[uvl].uv = (0.001, 0.001)
gme = bpy.data.meshes.new('glow'); bm.to_mesh(gme); bm.free()
gob = bpy.data.objects.new('glow', gme); scene.collection.objects.link(gob)
for m in body.data.materials:
    gme.materials.append(m)
for p, mi in zip(gme.polygons, mat_of):
    p.material_index = mi; p.use_smooth = mi == 1
for name in ('Body', 'Sensor'):
    g = gob.vertex_groups.new(name=name)
    verts = sorted({vi for p, b in zip(gme.polygons, bone_of) if b == name for vi in p.vertices})
    g.add(verts, 1.0, 'REPLACE')
gpart = gme.attributes.new('part', 'INT', 'FACE')
for p, b in zip(gme.polygons, bone_of):
    gpart.data[p.index].value = 1 if b == 'Body' else 2
for o in scene.objects:
    o.select_set(o in (body, gob))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='SHORT_EDGE')
bm.to_mesh(body.data); bm.free()
print('BUILD tris', len(body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=cc.path('work/build.blend'))
print('SAVED')
