"""The Gatekeeper's Bastion Emitter off the carbine and the body: search its turn about the left forearm's axis (the
socket's Z through the forearm centre, `orbit`, 0..345 deg in 15 deg steps) and its size (`scale` 1.0 .. 0.6, its inner
face kept on the forearm by `centre`) that minimise its intersections (BVH face-pair overlaps) with the carbine, the body
skin and the carapace over the set's final clip poses (the left forearm, hand and bracer it is worn on left out). The least change within 10 % of the best
count wins (the turn first, then the size); written into scripts/weapons.json. Run in work/assembly_gate.blend.
Args: -- <action:step> [<action:step> ...]"""
import bpy, sys, os, json
from pathlib import Path
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]
specs = [(x.split(':')[0], int(x.split(':')[1])) for x in sys.argv[sys.argv.index('--') + 1:]]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; BODY = bpy.data.objects['Body']
E = bpy.data.objects['W_bastion_emitter']; GUN = bpy.data.objects['W_lancer_carbine']
MOUNTS = json.loads((P / 'scripts' / 'weapons.json').read_text()); m0 = dict(MOUNTS['bastion_emitter'])
AXIS = (-0.13, 0.0)                                  # add_sockets.py: the socket sits 0.13 m out from the forearm's axis
SKIP = ('B_Wing_', 'B_L_Fore', 'B_L_Hand', 'B_L_Finger')
gi = {g.index: g.name for g in BODY.vertex_groups}
dom = [gi[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in BODY.data.vertices]
body_faces = [tuple(p.vertices) for p in BODY.data.polygons if not any(dom[i].startswith(SKIP) for i in p.vertices)]
others = [(o, None) for o in sc.objects if o.type == 'MESH' and o.name.startswith('Arm_') and o.name != 'Arm_bracer_L']
others += [(BODY, body_faces), (GUN, None)]
efaces = [tuple(p.vertices) for p in E.data.polygons]
cur_inv = cl.mount_matrix(m0).inverted()
frames = []
for act, step in specs:
    rig.animation_data.action = bpy.data.actions[act]
    f0, f1 = map(int, bpy.data.actions[act].frame_range)
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        co, fa = [], []
        for o, faces in others:
            e = o.evaluated_get(dg); me = e.to_mesh(); n = len(co)
            co += [o.matrix_world @ v.co for v in me.vertices]
            fa += [tuple(i + n for i in f_) for f_ in (faces or [tuple(p.vertices) for p in me.polygons])]
            e.to_mesh_clear()
        e = E.evaluated_get(dg); me = e.to_mesh(); eco = [E.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
        S = rig.matrix_world @ rig.pose.bones['Emitter_L'].matrix
        frames.append((BVHTree.FromPolygons(co, fa), S, eco, f'{act}:{f}'))


def centre(s):
    """the shrunk emitter kept on the forearm: its inner face (weapon +y -> socket -X, 0.096 m) stays where it was"""
    return [0.0, -0.096 * (1 - s) / s, 0.0]


def score(deg, s, detail=False):
    m = dict(m0, orbit=[deg, *AXIS], scale=s, centre=centre(s)); M = cl.mount_matrix(m) @ cur_inv
    tot, per = 0, []
    for tree, S, eco, name in frames:
        T = S @ M @ S.inverted()
        n = len(BVHTree.FromPolygons([T @ q for q in eco], efaces).overlap(tree)); tot += n
        if detail and n: per.append((name, n))
    return (tot, sorted(per, key=lambda x: -x[1])[:6]) if detail else tot


res = sorted((score(d, s), d, s) for d in range(0, 360, 15) for s in (1.0, 0.9, 0.8, 0.7, 0.6))
best = res[0][0]
pick = min((r for r in res if r[0] <= best * 1.1 + 2), key=lambda r: (min(r[1], 360 - r[1]) / 15 + (1.0 - r[2]) * 10))
print('FRAMES', len(frames), 'BEST', res[:5], flush=True)
print('BEFORE', score(0, 1.0, True), flush=True)
print('AFTER', pick[1:], score(pick[1], pick[2], True), flush=True)
if os.environ.get('WRITE'):
    MOUNTS['bastion_emitter'].update(orbit=[pick[1], *AXIS], scale=pick[2], centre=centre(pick[2]))
    (P / 'scripts' / 'weapons.json').write_text(json.dumps(MOUNTS, indent=1))
    print('WRITTEN', pick[1:], flush=True)
sys.stdout.flush(); os._exit(0)
