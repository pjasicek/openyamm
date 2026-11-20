"""hkr G6 for the skinned shell (Trooper caste; after hes_villager_f_claude/scripts/g6_leg_leak.py): on every frame of
every listed clip, the kept skin (not `shell_hidden`) that lies behind a shell piece at rest against the piece's
outer surface (the NV x NU outer grid of make_armour.py; an open shell for this test): proximity to the nearest outer
face signed by its normal; a skin vertex LEAKS when its signed distance exceeds LEAK and the offset runs along the
normal (tangential part < TANG: the vertex lies over the panel, not beside its edge). Candidates per piece: kept skin
of the piece's skin selection (spec exclude/include bones and pieces) within 6 cm behind the outer surface at rest and
over it. Prints per clip the worst leak per piece; writes review/shell_leak_<tag>.json. Pass: no leak.
Args: -- <blend> <spec json> <tag> <clip> [...]   (env LEAK m, default 0.005; TANG 0.004)"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, specp, tag, clips = a[0], a[1], a[2], a[3:]
LEAK, TANG = float(os.environ.get('LEAK', '0.005')), float(os.environ.get('TANG', '0.004'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(specp))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
nv = len(me.vertices)
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
HID = np.zeros(nv, np.int32); me.attributes['shell_hidden'].data.foreach_get('value', HID)


def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


def signed(tree, p):
    loc, n, fi, d = tree.find_nearest(Vector(p), 0.08)
    if loc is None: return None
    v = Vector(p) - loc; s_ = v.dot(n); t = (v - n * s_).length
    return s_, t


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
B0 = ev(body)
pieces = []
for pl in [p for p in SPEC['plates'] if p.get('shell')]:
    ob = bpy.data.objects['Arm_' + pl['name']]; NU, NV = pl.get('nu', 9), pl.get('nv', 8); G = NU * NV
    of = [tuple(p.vertices) for p in ob.data.polygons if all(x < G for x in p.vertices)]
    P0 = ev(ob); t0 = BVHTree.FromPolygons(P0.tolist(), of)
    xb = set(pl.get('exclude_bones', [])) | set(SPEC.get('exclude_bones_all', [])); xp = set(pl.get('exclude_pieces', []))
    ib = set(pl.get('include_bones', []))
    cand = []
    for i in range(nv):
        if HID[i] or DOM[i] in xb or PIECE[i] in xp or (ib and DOM[i] not in ib): continue
        r = signed(t0, B0[i])
        if r is not None and -0.06 < r[0] < 0 and r[1] < TANG: cand.append(i)
    pieces.append((pl['name'], ob, of, np.array(cand, int)))
rep = {}
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); worst = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); B = ev(body)
        for name, ob, of, cand in pieces:
            if not len(cand): continue
            t = BVHTree.FromPolygons(ev(ob).tolist(), of)
            for i in cand:
                r = signed(t, B[i])
                if r is not None and r[0] > LEAK and r[1] < TANG and r[0] > worst.get(name, [0])[0]:
                    worst[name] = [round(r[0] * 100, 2), f, DOM[i]]
    rep[clip] = worst
    print('SHELLLEAK', clip, 'FAIL' if worst else 'PASS', json.dumps(worst))
print('SHELLLEAK candidates', {n: len(c) for n, _, _, c in pieces})
json.dump(rep, open(os.path.join(HERE, 'review', f'shell_leak_{tag}.json'), 'w'), indent=1)
