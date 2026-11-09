"""Posed bow grip gate (from mm6_lzd_reduce_claude): body GLB + bow GLB, the bow at the Bow joint (glTF node frame
recovered from the inverse bind matrix), every 2nd frame of every clip. Hand vertices (hand/finger weights > 0.5) of
each hand within 1 cm of the bow surface are signed by the nearest bow face normal: inside = deeper than 1 mm,
contact = within 3 mm. Also records, in the bow's own space, the y range of the right-hand vertices within 4 cm of
the bow (the fist band: rings kept exactly) -> work/grip_<label>.json. Optional 4th argument: LOD level of the bow.
Usage: blender -b -P grip_gate_bow.py -- <body glb> <bow glb> <label> [bow lod]"""
import bpy, sys, json, struct, os, copy
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
body, bow, label = args[:3]; lod = int(args[3]) if len(args) > 3 else 0
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
from pathlib import Path
if lod:  # write the bow with the requested LOD as its node mesh
    D, Bn = read_glb(Path(bow)); n = next(x for x in D['nodes'] if 'mesh' in x)
    n['mesh'] = D['meshes'][n['mesh']]['extras']['openyamm_lods'][lod - 1]
    bow = os.path.join(HERE, 'work', f'grip_bow_lod{lod}.glb'); write_glb(Path(bow), D, Bn)
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Bow')].T)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(body))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = bpy.data.objects['M154']
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=os.path.abspath(bow))
bo = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH')
bo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Bow']
C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
# bow mesh vertices in the joint's own space: undo the import's own object transform (Y-up -> Z-up)
bverts = [bo.matrix_world @ v.co for v in bo.data.vertices]
tree = BVHTree.FromPolygons(bverts, [p.vertices for p in bo.data.polygons])
Ainv = Matrix(np.linalg.inv(A).tolist())
hands = {}
for side in ('R', 'L'):
    hg = {g.index for g in bodyo.vertex_groups if g.name.startswith(f'B_{side}_Hand') or g.name.startswith(f'B_{side}_Finger')}
    hands[side] = np.where([sum(g.weight for g in v.groups if g.group in hg) > .5 for v in bodyo.data.vertices])[0]
out = {}; band = []
for act in bpy.data.actions:
    arm.animation_data.action = act
    if len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    res = {s: dict(inside=0, contact=0, deepest_mm=0.0) for s in hands}; fr = 0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        Winv = (arm.matrix_world @ pbm.matrix @ C).inverted()
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        for side, ids in hands.items():
            for i in ids:
                p = bo.matrix_world @ (Winv @ (bodyo.matrix_world @ me.vertices[i].co))
                loc, nrm, _, dist = tree.find_nearest(p, 0.04)
                if loc is None:
                    continue
                s = (p - loc).dot(nrm)
                if side == 'R':
                    band.append((Ainv @ p).y)   # bow's own glTF frame (+Y along the bow)
                if dist > 0.01:
                    continue
                r = res[side]; r['inside'] += int(s < -.001); r['contact'] += int(abs(s) < .003)
                r['deepest_mm'] = round(min(r['deepest_mm'], s * 1000), 2)
        ev.to_mesh_clear(); fr += 1
    out[act.name] = dict(frames=fr, **{f'{s}_{k}': v for s in res for k, v in res[s].items()})
band = np.array(band)
rep = dict(label=label, lod=lod, hand_vertices={s: len(v) for s, v in hands.items()}, clips=out,
           right_band_y=[round(float(np.percentile(band, 0.5)), 4), round(float(np.percentile(band, 99.5)), 4),
                         round(float(band.min()), 4), round(float(band.max()), 4)] if len(band) else None)
json.dump(rep, open(os.path.join(HERE, 'work', f'grip_{label}.json'), 'w'), indent=1)
print('GRIP', json.dumps(rep))
