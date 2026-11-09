"""Where the arm-into-torso probe hits (m254 reduce): the arm vertices deeper than 1.5 cm with their rest positions and
the rest centre of the torso face they are behind. Args: -- <blend> <action> <side> <frame,...>
Arm-into-torso probe (m254: closed skin only) (user review 2026-10-20: the spearman's arm sank into the chest; the G6 gate samples only the
forearms and hands). Per action and frame, the deepest upper-arm / forearm vertex inside the torso: torso = faces whose
vertices are all weighted > 0.6 to the spine, pelvis, neck and head bones; a vertex is inside if it lies behind the
closest torso face within a 45 deg cone of its normal (the G6 test), up to 12 cm. Upper-arm vertices within 8 cm of
the shoulder joint are skipped (the shoulder blend). Prints per action and arm the worst depth and the frames above
1.5 cm. Args: -- <blend> <action> [...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); acts = a[1:2]; SIDE = a[2]; FR = [int(x) for x in a[3].split(',')]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
AXIAL = ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head')
nv = len(me.vertices)
ax = np.zeros(nv); part = {}
for s in 'LR':
    part[s] = {'upper': np.zeros(nv), 'fore': np.zeros(nv)}
for v in me.vertices:
    for e in v.groups:
        n = names[e.group]
        if n in AXIAL:
            ax[v.index] += e.weight
        for s in 'LR':
            if n.startswith(f'B_{s}_UpperArm'):
                part[s]['upper'][v.index] += e.weight
            if n.startswith(f'B_{s}_Forearm'):
                part[s]['fore'][v.index] += e.weight
# m254: only the CLOSED skin (garment 0) takes the inside test; the collar, nemes, belt and loincloth are open shells
# (any point behind a panel counted as 'inside': 11-12 cm hits at the search limit)
_gv = [0] * nv
if 'garment' in me.attributes:
    import numpy as _np; _g = _np.zeros(nv, _np.int32); me.attributes['garment'].data.foreach_get('value', _g); _gv = _g
tris = [tuple(p.vertices) for p in me.polygons if all(ax[i] > 0.6 for i in p.vertices) and _gv[p.vertices[0]] == 0]
rest = np.array([tuple(v.co) for v in me.vertices])
act = bpy.data.actions[acts[0]]; rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
for f in FR:
    sc.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear(); co = co.reshape(-1, 3)
    bvh = BVHTree.FromPolygons([Vector(c) for c in co], tris)
    sh = rig.pose.bones[f'B_{SIDE}_UpperArm'].head
    idx = np.where(part[SIDE]['upper'] > 0.5)[0]; idx = idx[np.linalg.norm(co[idx] - np.array(sh), axis=1) > 0.08]
    hits = []
    for i in idx:
        p = Vector(co[i]); hit = bvh.find_nearest(p, 0.12)
        if hit[0] is None:
            continue
        d = p - hit[0]; L = d.length
        if L > 0.015 and d.dot(hit[1]) < -0.7 * L:
            t = tris[hit[2]]; hits.append((L, i, rest[list(t)].mean(0)))
    hits.sort(key=lambda x: -x[0])
    print('WHERE', f, len(hits), 'arm verts > 1.5 cm', ' | '.join(f'{L*100:.1f}cm v{i} rest {np.round(rest[i], 3).tolist()} torso face {np.round(c, 3).tolist()}' for L, i, c in hits[:6]))
