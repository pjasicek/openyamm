"""G6 contacts: per frame of each action, how deep the forearms, hands (with fingers) and the sword blade go into the
rest of the body (torso, hips, legs, armour; the arm's own side excluded). Inside test: closest point on the posed
body BVH and its face normal; a sample is inside if it lies behind the closest face within a 45 deg cone of its normal
((p - closest) . normal < -0.7 |p - closest|, within 5 cm); a plain sign test flagged points beside thin belts. Sword: points along the
handle axis (work/grip_pose.json, hand-local) from the guard (+6 cm) to the tip (+85 cm), blade on the axis' positive
side. Prints per action the worst depth (cm) and frame for each part, and writes work/g6_contacts.json.
Args: -- <blend> action [action ...]"""
import bpy, sys, os, json
import numpy as np
from volume_contact import inside
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work','rig_v15.blend') if blend.lower().endswith('.glb') else os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if blend.lower().endswith('.glb'):
    from mathutils.kdtree import KDTree
    pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
    kd=KDTree(len(me.vertices))
    for v in me.vertices:kd.insert(body.matrix_world@v.co,v.index)
    kd.balance()
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=os.path.abspath(blend))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    body=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));me=body.data
    labels=[int(pv[kd.find(body.matrix_world@v.co)[1]]) for v in me.vertices]
    sg=body.vertex_groups['Sword'].index
    for v in me.vertices:
        if any(e.group==sg and e.weight>.5 for e in v.groups):labels[v.index]=999
    me.attributes.new('piece','INT','POINT').data.foreach_set('value',labels)
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
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {}
    for f in np.arange(f0,f1+1e-6,bpy.context.scene.render.fps/48):
        bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)))
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        for s in ('L', 'R'):
            keep = ~PARTS[f'{s}_arm_all'] & (PIECE!=999)
            fl = [fc for fc in faces if all(keep[i] for i in fc)]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm']], f'{s}_hand': P[PARTS[f'{s}_hand']]}
            if s == 'R':
                hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
                c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
                samples['sword'] = np.array([tuple(c + ax * t) for t in np.linspace(0.06, 0.85, 40)])
            if s == 'R':
                # longest blade that stays out of the body in this frame: first sample (beyond the guard) inside
                for t, p in zip(np.linspace(0.06, 0.85, 40), samples['sword']):
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree,p):
                        if t < worst.get('max_clear_blade_m', (9, 0))[0]:
                            worst['max_clear_blade_m'] = (float(t), f)
                        break
            for k, pts in samples.items():
                d, hit_piece = 0.0, None
                for p in pts:
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree,p):   # behind the face, not beside a thin edge
                        d = dist; hit_piece = int(PIECE[fl[idx][0]])
                if d > worst.get(k, (0, 0))[0]:
                    worst[k] = (d, f, hit_piece)
    report[an] = {k: ((round(v[0], 2) if k == 'max_clear_blade_m' else round(v[0] * 100, 4)),) + tuple(float(x) if isinstance(x,np.floating) else x for x in v[1:]) for k, v in worst.items()}
    print('G6', an, 'worst depth cm (frame, piece hit):', report[an])
json.dump(report, open(os.path.join(HERE, 'work', 'g6_contacts.json'), 'w'), indent=1)
