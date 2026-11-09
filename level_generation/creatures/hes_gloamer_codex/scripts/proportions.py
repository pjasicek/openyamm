"""G2 / H2: segment proportions of a rig, normalised by standing height, for comparison with the source set.
Source mode reads the set's armature (joint heads only; imported tails are unusable) and the height of its own
character mesh. Target mode reads a project blend (armature + mesh by name). Writes/compares work/proportions.json.
Args: -- source <set glb>          |  -- target <blend> <armature> <mesh> <bone map json>"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'proportions.json')
SEG = {   # name -> (joint A, joint B) in source names; the target uses the same names through its bone map
    'shoulder_width': ('B_L_UpperArm', 'B_R_UpperArm'), 'clavicle_R': ('B_R_Clavicle', 'B_R_UpperArm'),
    'upper_arm_R': ('B_R_UpperArm', 'B_R_Forearm'), 'forearm_R': ('B_R_Forearm', 'B_R_Hand'),
    'hand_R': ('B_R_Hand', 'B_R_Finger2'), 'hip_width': ('B_L_Thigh', 'B_R_Thigh'),
    'thigh_R': ('B_R_Thigh', 'B_R_Calf'), 'shin_R': ('B_R_Calf', 'B_R_Foot'),
    'pelvis_to_neck': ('B_Pelvis', 'B_Neck'), 'neck_to_head': ('B_Neck', 'B_Head'),
}
HEIGHTS = {'shoulder_height': 'B_R_UpperArm', 'hip_height': 'B_R_Thigh', 'pelvis_height': 'B_Pelvis'}


def measure(arm, mesh, name):
    W = arm.matrix_world
    pos = lambda b: np.array(W @ arm.data.bones[name(b)].head_local)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(deps); me = ev.to_mesh()
    z = np.array([(mesh.matrix_world @ v.co).z for v in me.vertices]); ev.to_mesh_clear()
    H = z.max() - z.min()
    r = {'height_m': round(float(H), 4)}
    for k, (p, q) in SEG.items():
        r[k] = round(float(np.linalg.norm(pos(p) - pos(q)) / H), 4)
    for k, b in HEIGHTS.items():
        r[k] = round(float((pos(b)[2] - z.min()) / H), 4)
    return r


if a[0] == 'source':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[1]))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent is arm)
    res = measure(arm, mesh, lambda b: b)
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    data['source'] = res
    json.dump(data, open(OUT, 'w'), indent=1)
    print('SOURCE', json.dumps(res))
else:
    blend, arm_name, mesh_name, mapping = a[1:5]
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    arm, mesh = bpy.data.objects[arm_name], bpy.data.objects[mesh_name]
    m = json.load(open(mapping))
    res = measure(arm, mesh, lambda b: m[b])
    data = json.load(open(OUT)); data['target'] = res
    json.dump(data, open(OUT, 'w'), indent=1)
    src = data['source']
    for k in res:
        if k != 'height_m':
            print(f'PROP {k:16s} source {src[k]:.3f} target {res[k]:.3f} ratio {res[k] / src[k]:.2f}')

sys.stdout.flush();sys.stderr.flush();os._exit(0)
