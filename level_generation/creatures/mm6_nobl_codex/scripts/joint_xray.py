"""G3 X-ray: the mesh semi-transparent (wireframe overlay) with each fitted joint as a coloured sphere and the limb
segments as rods; front and left views, plus close-ups of each arm. Args: -- <blend> <mesh> <joints json> <out prefix>"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a_ = sys.argv[sys.argv.index('--') + 1:]
blend, mesh, jpath, out = a_[:4]
second = a_[4] if len(a_) > 4 else None   # optional second joint set, drawn as small black spheres
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
J = {k: Vector(v) for k, v in json.load(open(jpath))['joints'].items()}
ob = bpy.data.objects[mesh]
mat = bpy.data.materials.new('ghost'); mat.diffuse_color = (0.8, 0.8, 0.8, 0.25)
ob.data.materials.clear(); ob.data.materials.append(mat); ob.show_wire = True
cols = {'Arm': (0.9, 0.2, 0.2, 1), 'Forearm': (0.2, 0.8, 0.2, 1), 'Hand': (0.2, 0.4, 0.95, 1), 'Thigh': (0.9, 0.7, 0.1, 1),
        'Calf': (0.8, 0.3, 0.9, 1), 'Foot': (0.1, 0.8, 0.8, 1)}


def sphere(p, r, c):
    me = bpy.data.meshes.new('j'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('j', me); bpy.context.scene.collection.objects.link(o); o.location = p
    m = bpy.data.materials.new('c'); m.diffuse_color = c; me.materials.append(m)


def rod(a, b, c):
    me = bpy.data.meshes.new('r'); bm = bmesh.new()
    L = (b - a).length
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.006, radius2=0.006, depth=L)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('r', me); bpy.context.scene.collection.objects.link(o)
    o.location = (a + b) / 2; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    m = bpy.data.materials.new('c'); m.diffuse_color = c; me.materials.append(m)


for k, p in J.items():
    c = next((v for t, v in cols.items() if k.endswith(t)), (1, 1, 1, 1))
    sphere(p, 0.018, c)
if second:
    for k, p in json.load(open(second))['joints'].items():
        sphere(Vector(p), 0.011, (0.02, 0.02, 0.02, 1))
for s in ('R', 'L'):
    for a, b in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')):
        if f'{s}_{a}' in J and f'{s}_{b}' in J:
            rod(J[f'{s}_{a}'], J[f'{s}_{b}'], (0.1, 0.1, 0.1, 1))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.35
H = json.load(open(jpath))['height_m']
import os as _o
if _o.environ.get("XC"):
    exec(open(_o.environ["XC"]).read()); raise SystemExit
common.render_views(out, H / 2, H * 1.18, views=('front', 'left'), resolution=(900, 900))
for s in ('R', 'L'):
    c = (J[f'{s}_UpperArm'] + J[f'{s}_Hand']) / 2
    common.render_views(f'{out}_{s}arm', c.z, H * 0.5, views=('front',), resolution=(600, 600), target=(c.x, c.y))
