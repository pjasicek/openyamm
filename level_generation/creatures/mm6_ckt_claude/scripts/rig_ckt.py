"""Cockatrice rig from the Meshy Smart Topology mesh. Saves work/rig_v1.blend. Forward -Y, up +Z, creature's left +X.

Body joints come from scripts/analyse.py (midline z-range per y, leg centroids per z); wing joints are given as
front-view (x, z) and their y is sampled from the wing sheet (the wings stand as a near-vertical sheet at y ~ -0.24),
so the bones lie inside the membrane. Coordinates are in the Meshy frame; the mesh is grounded (min z = 0) after.
Bones:
  Hips (root) -> Chest -> Neck1 -> Neck2 -> Head
  Hips -> Tail1..Tail7
  Chest -> UpperArm/ForeArm (wing arm) -> Finger1..3 a/b (bat fingers fanning from the wrist)
  Hips -> Thigh -> Shin -> Tarsus -> Foot  (bird leg: knee forward, hock back, foot forward)
Blender automatic weights, then the separate pieces (wing leading-edge bones, ruff feathers) are rebound to the main
body: long pieces per vertex (nearest main vertex), small pieces rigidly (nearest attachment). The stray fragment
floating beside the right foot is deleted."""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Cockatrice'
label = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
STRAY = 29
VOXEL = 0.004   # metres; thin enough to keep the wing membranes
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(label == STRAY)[0]], context='VERTS')
bm.to_mesh(mesh.data); bm.free()
label = label[label != STRAY]
co = np.array([tuple(v.co) for v in mesh.data.vertices])
Z0 = float(co[:, 2].min())
for v in mesh.data.vertices:
    v.co.z -= Z0
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in mesh.data.vertices])
main = label == 0


def B(x, y, z):
    return Vector((x, y, z - Z0))


def W(x, z, r=0.015):
    """Wing joint at front-view (x, z): y = median y of the main-mesh vertices within r in x and z."""
    zz = z - Z0
    m = main & (np.abs(co[:, 0] - x) < r) & (np.abs(co[:, 2] - zz) < r)
    if m.sum() < 3:
        m = main & (np.hypot(co[:, 0] - x, co[:, 2] - zz) < 0.04)
    return Vector((x, float(np.median(co[m, 1])), zz))


CHAINS = {'Spine': (None, [B(0, -0.16, -0.02), B(0, -0.22, 0.04), B(0, -0.29, 0.11)]),
          'Neck': ('Chest', [B(0, -0.29, 0.11), B(0, -0.355, 0.12), B(0, -0.415, 0.13)]),
          'Head': ('Neck2', [B(0, -0.415, 0.13), B(0, -0.50, 0.112)]),
          'Tail': ('Hips', [B(0, -0.16, -0.02), B(0, -0.10, -0.083), B(0, -0.02, -0.107), B(0, 0.06, -0.131),
                            B(0, 0.14, -0.154), B(0, 0.22, -0.164), B(0, 0.31, -0.170), B(0, 0.40, -0.176),
                            B(0, 0.50, -0.174)])}
NAMES = {'Spine': ['Hips', 'Chest'], 'Neck': ['Neck1', 'Neck2'], 'Head': ['Head'],
         'Tail': [f'Tail{i}' for i in range(1, 9)]}
FINGERS = (((0.36, 0.20), (0.505, 0.125)), ((0.33, 0.14), (0.44, 0.065)), ((0.29, 0.11), (0.36, 0.03)))
for side, s in (('L', 1), ('R', -1)):
    wrist = W(s * 0.215, 0.215)
    CHAINS['Arm_' + side] = ('Chest', [W(s * 0.07, 0.115), W(s * 0.17, 0.14), wrist])
    NAMES['Arm_' + side] = [f'UpperArm_{side}', f'ForeArm_{side}']
    for k, (mid, tip) in enumerate(FINGERS):
        CHAINS[f'Finger{k + 1}_{side}'] = (f'ForeArm_{side}', [wrist, W(s * mid[0], mid[1]), W(s * tip[0], tip[1])])
        NAMES[f'Finger{k + 1}_{side}'] = [f'Finger{k + 1}a_{side}', f'Finger{k + 1}b_{side}']
    CHAINS['Leg_' + side] = ('Hips', [B(s * 0.05, -0.21, -0.03), B(s * 0.057, -0.255, -0.095),
                                      B(s * 0.069, -0.186, -0.14), B(s * 0.073, -0.215, -0.19),
                                      B(s * 0.078, -0.295, -0.212)])
    NAMES['Leg_' + side] = [f'Thigh_{side}', f'Shin_{side}', f'Tarsus_{side}', f'Foot_{side}']

arm_data = bpy.data.armatures.new('Ckt_Rig')
rig = bpy.data.objects.new('Ckt_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head', 'Tail'] + [f'{k}_{s}' for s in 'LR' for k in ('Arm', 'Finger1', 'Finger2', 'Finger3', 'Leg')]
for key in order:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]; b.tail = pts[i + 1]
        b.align_roll(Vector((0, 0, 1)) if abs((pts[i + 1] - pts[i]).normalized().z) < 0.9 else Vector((0, -1, 0)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
# Heat weighting fails on the Meshy mesh itself (thin membranes, loose and overlapping pieces). Solve it on a
# watertight voxel-remeshed proxy of the main body instead, at 10x scale, then copy the weights to the real mesh by
# nearest surface point (Data Transfer, face-interpolated).
proxy = mesh.copy(); proxy.data = mesh.data.copy(); proxy.name = 'WeightProxy'
bpy.context.scene.collection.objects.link(proxy)
pbm = bmesh.new(); pbm.from_mesh(proxy.data); pbm.verts.ensure_lookup_table()
bmesh.ops.delete(pbm, geom=[pbm.verts[i] for i in np.nonzero(~main)[0]], context='VERTS')
pbm.to_mesh(proxy.data); pbm.free()
for o in (proxy, rig):
    o.scale = (10, 10, 10)
bpy.context.view_layer.objects.active = proxy
for o in bpy.data.objects:
    o.select_set(o == proxy)
bpy.ops.object.transform_apply(scale=True)
rem = proxy.modifiers.new('Remesh', 'REMESH'); rem.mode = 'VOXEL'; rem.voxel_size = VOXEL * 10
bpy.ops.object.modifier_apply(modifier='Remesh')
print('PROXY verts', len(proxy.data.vertices))
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
proxy.parent = None
bpy.context.view_layer.objects.active = proxy
for o in bpy.data.objects:
    o.select_set(o == proxy)
proxy.modifiers.clear()
proxy.scale = (0.1, 0.1, 0.1); rig.scale = (1, 1, 1)
bpy.ops.object.transform_apply(scale=True)
print('PROXY unweighted', sum(1 for v in proxy.data.vertices if not v.groups))
for b in arm_data.bones:
    mesh.vertex_groups.new(name=b.name)
dt = mesh.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.modifier_apply(modifier='DT')
bpy.data.objects.remove(proxy, do_unlink=True)
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig

# Separate pieces: rebind to the main body.
verts = mesh.data.vertices
main_idx = np.nonzero(main)[0]
tree = kdtree.KDTree(len(main_idx))
for i in main_idx:
    tree.insert(verts[int(i)].co, int(i))
tree.balance()
groups = mesh.vertex_groups


def copy_weights(dst, src):
    for g in list(verts[dst].groups):
        groups[g.group].remove([dst])
    for g in verts[src].groups:
        groups[g.group].add([dst], g.weight, 'REPLACE')


pieces = {}
for i, k in enumerate(label):
    if k != 0:
        pieces.setdefault(int(k), []).append(i)
long_pieces = 0
for k, idx in pieces.items():
    p = co[idx]
    if np.ptp(p, axis=0).max() > 0.08:
        long_pieces += 1
        for i in idx:
            copy_weights(i, tree.find(verts[i].co)[1])
    else:
        anchor = min((tree.find(verts[i].co) for i in idx), key=lambda hit: hit[2])[1]
        for i in idx:
            copy_weights(i, anchor)
# Vertices the proxy left without weights take those of the nearest weighted vertex.
weighted = [v.index for v in verts if v.groups]
wtree = kdtree.KDTree(len(weighted))
for i in weighted:
    wtree.insert(verts[i].co, i)
wtree.balance()
for v in [v for v in verts if not v.groups]:
    copy_weights(v.index, wtree.find(v.co)[1])
empty = [v.index for v in verts if not v.groups]
print('RIGGED bones', len(arm_data.bones), 'unweighted', len(empty), 'pieces', len(pieces), 'long', long_pieces,
      'Z0', round(Z0, 4))
json.dump({'Z0': Z0, 'joints': {k: [list(map(lambda x: round(x, 4), p)) for p in v[1]] for k, v in CHAINS.items()}},
          open(os.path.join(HERE, 'work', 'rig_info.json'), 'w'), indent=1)
np.save(os.path.join(HERE, 'work', 'rig_labels.npy'), label)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
