"""Bloodsucker: import the Meshy Smart Topology mesh, ground it (lowest point z=0), build a winged-serpent skeleton and
skin it with Blender automatic (heat) weights. Body joints are read from gridded orthographic views (Meshy frame);
wing joints are given as front-view (x, z) with y sampled from the membrane so the bones lie in the sheet.
Saves work/rig_v1.blend. Forward -Y, up +Z, character left +X."""
import bpy, os
import numpy as np
from mathutils import Vector

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
co = np.array([tuple(v.co) for v in mesh.data.vertices])
Z0 = co[:, 2].min()
mesh.location.z -= Z0
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Bld'
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in mesh.data.vertices])


def B(y, z, x=0.0):                  # body joints in the original Meshy frame
    return Vector((x, y, z - Z0))


def W(x, z, r=0.015):                # wing joints: y sampled from the wing sheet near (x, z)
    zz = z - Z0
    m = (np.abs(co[:, 0] - x) < r) & (np.abs(co[:, 2] - zz) < r)
    if m.sum() < 2:
        m = np.linalg.norm(co[:, [0, 2]] - (x, zz), axis=1) < 0.04
    return Vector((x, float(np.median(co[m, 1])), zz))


CHAINS = {'Spine': (None, [B(0.04, -0.19), B(-0.08, -0.16), B(-0.18, -0.12)]),
          'Neck': ('Spine2', [B(-0.18, -0.12), B(-0.26, -0.075), B(-0.33, -0.04)]),
          'Head': ('Neck2', [B(-0.33, -0.04), B(-0.44, -0.005)]),
          'Mouth': ('Head', [B(-0.44, -0.005), B(-0.50, 0.0)]),
          'Tail': ('Spine1', [B(0.04, -0.19), B(0.12, -0.19), B(0.20, -0.19), B(0.28, -0.185), B(0.36, -0.17),
                              B(0.43, -0.14), B(0.50, -0.09)])}
NAMES = {'Spine': ['Spine1', 'Spine2'], 'Neck': ['Neck1', 'Neck2'], 'Head': ['Head'], 'Mouth': ['Mouth'],
         'Tail': [f'Tail{i}' for i in range(1, 7)]}
for side, s in (('L', 1), ('R', -1)):
    sh = B(-0.07, -0.12, s * 0.06)
    elbow = W(s * 0.10, 0.07)
    CHAINS['Arm_' + side] = ('Spine2', [sh, elbow, W(s * 0.17, 0.21), W(s * 0.285, 0.30)])
    NAMES['Arm_' + side] = [f'UpperArm_{side}', f'ForeArm_{side}', f'Hand_{side}']
    for k, tip in enumerate(((0.27, 0.06), (0.17, -0.03))):
        mid = ((0.10 + tip[0]) / 2, (0.07 + tip[1]) / 2)
        CHAINS[f'Finger{k + 1}_{side}'] = (f'UpperArm_{side}', [elbow, W(s * mid[0], mid[1]), W(s * tip[0], tip[1])])
        NAMES[f'Finger{k + 1}_{side}'] = [f'Finger{k + 1}a_{side}', f'Finger{k + 1}b_{side}']
    CHAINS['Front_' + side] = ('Spine2', [B(-0.10, -0.18, s * 0.055), B(-0.16, -0.215, s * 0.07)])
    NAMES['Front_' + side] = [f'FrontLeg_{side}']
    CHAINS['Hind_' + side] = ('Spine1', [B(0.0, -0.21, s * 0.06), B(0.02, -0.285, s * 0.07)])
    NAMES['Hind_' + side] = [f'HindLeg_{side}']

arm_data = bpy.data.armatures.new('Bld_Rig')
rig = bpy.data.objects.new('Bld_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head', 'Mouth', 'Tail'] + [f'{k}_{s}' for s in 'LR'
                                                      for k in ('Arm', 'Finger1', 'Finger2', 'Front', 'Hind')]
for key in order:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]; b.tail = pts[i + 1]
        b.align_roll(Vector((0, 0, 1)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# Separate pieces (dorsal spikes, mouth tentacles, wing thumbs) get mixed heat weights and drift off; bind each one
# rigidly to the main-body vertex nearest to it (where it attaches).
import bmesh
from mathutils import kdtree
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = [False] * len(bm.verts); islands = []
for v in bm.verts:
    if seen[v.index]:
        continue
    stack = [v]; comp = []; seen[v.index] = True
    while stack:
        a = stack.pop(); comp.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if not seen[b.index]:
                seen[b.index] = True; stack.append(b)
    islands.append(comp)
bm.free()
islands.sort(key=len, reverse=True)
verts = mesh.data.vertices
tree = kdtree.KDTree(len(islands[0]))
for i in islands[0]:
    tree.insert(verts[i].co, i)
tree.balance()
for comp in islands[1:]:
    anchor = min((tree.find(verts[i].co) for i in comp), key=lambda hit: hit[2])[1]
    weights = [(g.group, g.weight) for g in verts[anchor].groups]
    for group in mesh.vertex_groups:
        group.remove(comp)
    for gi, w in weights:
        mesh.vertex_groups[gi].add(comp, w, 'REPLACE')
print('ISLANDS rebound', len(islands) - 1)
empty = [v.index for v in mesh.data.vertices if not v.groups]
print('RIGGED bones', len(arm_data.bones), 'unweighted verts', len(empty))
for k in ('Arm_L', 'Finger1_L', 'Finger2_L'):
    print('JOINTS', k, [tuple(round(c, 3) for c in p) for p in CHAINS[k][1]])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
