"""Sample both forearms, hands and the actual staff against the other body parts at 48 Hz.
Report each part explicitly, including zero penetration. Sleeve wall crossings have a separate gate.
Args: -- <blend> action [action ...]
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
GP = os.path.join(HERE, 'work', 'grip_pose.json')
G = json.load(open(GP)) if os.path.exists(GP) else None    # druidess: no held prop
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
# These are hollow garment shells, not the solid opposite forearm. Their deliberate cuff overlap and hand
# enclosure are tested independently against the actual triangles by review1_occlusion.py.
REST = np.array([v.co[:] for v in me.vertices])
SLEEVE = (PIECE == 0) & (np.abs(REST[:, 0] + .006) > .22)
def inside(tree,x):
 direction=Vector((.811,.357,.463)).normalized();origin=Vector(x);hits=0
 for _ in range(64):
  hit=tree.ray_cast(origin,direction,5)[0]
  if hit is None:return hits%2==1
  hits+=1;origin=hit+direction*.000001
 raise AssertionError('Unresolved ray traversal')
FACE_CACHE={}
for s in ['L','R']:
 keep=~PARTS[f'{s}_arm_all'] & ~SLEEVE & (PIECE!=100)
 FACE_CACHE[s]=([fc for fc in faces if all(keep[i] for i in fc)],[fc for fc in faces if all(PIECE[i] not in [100,(2 if s=='L' else 3)] for i in fc)])
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {k: (0.0, 0.0, None) for k in ['L_forearm','R_forearm','L_hand','R_hand','staff']}
    for f in sorted(set(list(np.arange(f0, f1 + .0001, 30/48))+[float(f1)])):
        bpy.context.scene.frame_set(int(f), subframe=float(f % 1))
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        for s in ('L', 'R'):
            keep = ~PARTS[f'{s}_arm_all'] & ~SLEEVE & (PIECE != 100)     # druidess: the cloak is simulated (cloak_sim.py, own gate)
            fl,closed_faces=FACE_CACHE[s]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            closed=BVHTree.FromPolygons([tuple(p) for p in P],closed_faces)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm'] & np.isin(PIECE,[2,3])], f'{s}_hand': P[PARTS[f'{s}_hand'] & np.isin(PIECE,[2,3])]} 
            if s == 'R' and 'StaffMesh' in bpy.data.objects:
                obj=bpy.data.objects['StaffMesh'];evp=obj.evaluated_get(deps);mp=evp.to_mesh();samples['staff']=np.array([tuple(obj.matrix_world@v.co) for v in mp.vertices]);evp.to_mesh_clear()
            if s=='R' and np.any(PIECE==100):samples['staff']=P[PIECE==100]
            for k, pts in samples.items():
                assert len(pts)>0,(an,k,"empty contact sample")
                d, hit_piece = 0.0, None
                for sample_i, p in enumerate(pts):
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(closed,p):   # behind the face, not beside a thin edge
                        d = dist; hit_piece = int(PIECE[fl[idx][0]]); hit_face = list(fl[idx]); hit_sample = int(sample_i)
                if d > worst.get(k, (0, 0))[0]:
                    worst[k] = (d, f, hit_piece)
                    if d > .002 and os.environ.get('CONTACT_DETAIL'): print('CONTACT_DETAIL',an,k,f,round(d*1000,2),'body_rest', [list(me.vertices[i].co) for i in hit_face], 'sample',hit_sample)
    report[an] = {k: ((round(v[0], 2) if k == 'max_clear_blade_m' else round(v[0] * 100, 2)),) + tuple(v[1:]) for k, v in worst.items()}
    print('G6', an, 'worst depth cm (frame, piece hit):', report[an])
json.dump(report, open(os.path.join(HERE, os.environ.get('G6_REPORT','work/g6_contacts.json')), 'w'), indent=1)
