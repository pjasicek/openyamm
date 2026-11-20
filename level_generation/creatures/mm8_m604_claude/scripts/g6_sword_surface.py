"""G6 contacts: per frame of each action, how deep the forearms, hands (with fingers) and the sword blade go into the
rest of the body (torso, hips, legs, armour; the arm's own side excluded). Inside test: closest point on the posed
body BVH and its face normal; a sample is inside if it lies behind the closest face within a 45 deg cone of its normal
((p - closest) . normal < -0.7 |p - closest|, within 5 cm); a plain sign test flagged points beside thin belts. Sword: points along the
handle axis (work/grip_pose.json, hand-local) from the guard (+6 cm) to the tip (+85 cm), blade on the axis' positive
side. Prints per action the worst depth (cm) and frame for each part, and writes work/g6_contacts.json.
Args: -- <blend> action [action ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['EtherKnight']; me = body.data
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
names = [g.name for g in body.vertex_groups]
nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
col = {n: i for i, n in enumerate(names)}
def part(side, keys):
    return Wt[:, [col[n] for n in names if n.startswith(f'B_{side}_') and any(k in n for k in keys)]].sum(1)
PARTS = {}
for s in ('L', 'R'):
    PARTS[f'{s}_forearm'] = part(s, ('Forearm',)) > 0.5
    PARTS[f'{s}_hand'] = part(s, ('Hand', 'Finger')) > 0.5
    PARTS[f'{s}_arm_all'] = part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2
faces = [tuple(p.vertices) for p in me.polygons]
with bpy.data.libraries.load(os.path.join(HERE,'work','ready_final.blend'),link=False) as (source,dst):dst.meshes=['Body']
ref=dst.meshes[0];PIECE=np.full(nv,-1,np.int32)
assert len(ref.vertices)<nv and max((me.vertices[i].co-v.co).length for i,v in enumerate(ref.vertices))<1e-6
PIECE[:len(ref.vertices)]=[x.value for x in ref.attributes['piece'].data]
SWORD=Wt[:,col['Sword']]>.9
LOCAL=np.array([rig.data.bones['Sword'].matrix_local.inverted()@v.co for v in me.vertices]);BLADE=SWORD&(LOCAL[:,1]>.09)
def inside(tree,point):
    # Nearest-normal proximity alone falsely marks points behind a thin blade as penetrating it.
    votes=0
    for axis in [(1,.271,.137),(-.193,1,.317),(.239,.173,1)]:
        direction=Vector(axis).normalized();start=Vector(point);hits=0
        for _ in range(64):
            hit,normal,index,distance=tree.ray_cast(start,direction,10)
            if hit is None:break
            hits+=1;start=hit+direction*.00001
        else:raise AssertionError('Ray did not leave the mesh')
        votes+=hits%2
    return votes>=2
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {};lowest_sword=(9,0)
    for f in np.arange(f0, f1 + 0.01, 0.5):
        bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        if P[SWORD,2].min()<lowest_sword[0]:lowest_sword=(float(P[SWORD,2].min()),float(f))
        for s in ('L', 'R'):
            keep = ~PARTS[f'{s}_arm_all']
            if s=='R':keep &= ~SWORD
            fl = [fc for fc in faces if all(keep[i] for i in fc)]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm']], f'{s}_hand': P[PARTS[f'{s}_hand']]}
            if s == 'R':
                hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
                c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
                samples['sword'] = P[BLADE]
            for k, pts in samples.items():
                d, hit_piece = 0.0, None
                for p in pts:
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree,p):   # behind the face, not beside a thin edge
                        d = dist; hit_piece = int(PIECE[fl[idx][0]])
                if d > worst.get(k, (0, 0))[0]:
                    worst[k] = (d, f, hit_piece)
    report[an] = {k: ((round(v[0], 2) if k == 'max_clear_blade_m' else round(v[0] * 100, 1)),) + tuple(v[1:]) for k, v in worst.items()}
    print('SWORD_FLOOR',an,lowest_sword)
    print('G6', an, 'worst depth cm (frame, piece hit):', report[an])
json.dump(report, open(os.path.join(HERE, 'work', 'g6_sword_surface.json'), 'w'), indent=1)
