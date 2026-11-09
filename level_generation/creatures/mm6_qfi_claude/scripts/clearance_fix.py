"""Rock clearance on work/anim_v4.blend (in place): per clip and frame, the smallest forward tip of the abdomen chain
(world rotation about X, spread evenly over Abdomen2..Abdomen6, each about its own head) that keeps the queen's upper
body, arms and head out of the posed rock (inside test as rock_gate.py: an odd number of rock hits along -Y; abdomen
vertices are not tested: her abdomen rests in the niche, and in Death she sinks into the collapsing rock). Search:
0, then 3 deg steps up to MAX_DEG, refined to 1 deg. The per-frame angles are max-filtered over +-4 frames and
smoothed (Gaussian, sigma 2 frames) so the correction eases in and out; one-shot clips keep 0 at both ends when
those frames are clear. Writes work/clearance.json."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]
MAX_DEG = 30.0
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; rock = bpy.data.objects['Rock']
scene = bpy.context.scene
gi = {g.index: g.name for g in queen.vertex_groups}
dom = [gi[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '' for v in queen.data.vertices]
test = np.array([not d.startswith('Abdomen') for d in dom])
test_ids = np.where(test)[0][::2]                      # every second upper-body vertex for the search
CHAIN = [f'Abdomen{i}' for i in range(2, 7)]
DIR = Vector((0, -1, 0))


def rock_tree():
    deps = bpy.context.evaluated_depsgraph_get()
    rm = rock.evaluated_get(deps).to_mesh()
    bm = bmesh.new(); bm.from_mesh(rm); bm.transform(rock.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); rock.evaluated_get(deps).to_mesh_clear()
    return t


def max_depth(tree, ids):
    deps = bpy.context.evaluated_depsgraph_get()
    qm = queen.evaluated_get(deps).to_mesh()
    W = queen.matrix_world
    worst = 0.0
    for i in ids:
        p = W @ qm.vertices[int(i)].co
        o = p.copy(); hits = 0; first = None
        for _ in range(10):
            loc, nrm, idx, dist = tree.ray_cast(o, DIR, 50.0)
            if loc is None:
                break
            hits += 1
            if first is None:
                first = (loc - p).length
            o = loc + DIR * 1e-4
        if hits % 2 == 1:
            worst = max(worst, first)
    queen.evaluated_get(deps).to_mesh_clear()
    return worst


def apply_tip(base, deg):
    """Restore the chain's base pose, then tip it forward by deg in total."""
    for n in CHAIN:
        rig.pose.bones[n].matrix_basis = base[n]
    bpy.context.view_layer.update()
    a = math.radians(deg) / len(CHAIN)
    for n in CHAIN:
        pb = rig.pose.bones[n]
        M = rig.matrix_world @ pb.matrix
        h = M.translation.copy()
        M = Matrix.Translation(h) @ Matrix.Rotation(a, 4, 'X') @ Matrix.Translation(-h) @ M
        pb.matrix = rig.matrix_world.inverted() @ M
        bpy.context.view_layer.update()


report = {}
for name in ('Standing', 'Attack', 'Cast', 'Hit', 'Death'):
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    step = 3 if name == 'Standing' else 1
    frames = list(range(f0, f1 + 1, step))
    if frames[-1] != f1:
        frames.append(f1)
    need = []
    bases = {}
    for f in frames:
        scene.frame_set(f)
        base = {n: rig.pose.bones[n].matrix_basis.copy() for n in CHAIN}
        bases[f] = base
        rig.animation_data.action = None
        apply_tip(base, 0.0)
        tree = rock_tree()
        deg = 0.0
        if max_depth(tree, test_ids) > 0.01:
            deg = MAX_DEG
            for d in np.arange(3.0, MAX_DEG + 0.1, 3.0):
                apply_tip(base, d)
                if max_depth(tree, test_ids) <= 0.01:
                    deg = d
                    for d2 in np.arange(d - 2.0, d, 1.0):
                        apply_tip(base, d2)
                        if max_depth(tree, test_ids) <= 0.01:
                            deg = d2
                            break
                    break
        need.append(deg + (1.0 if deg > 0 else 0.0))      # 1 deg margin
        rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    need = np.array(need)
    # interpolate to every frame, max filter +-4, Gaussian sigma 2
    allf = np.arange(f0, f1 + 1)
    dense = np.interp(allf, frames, need)
    mx = np.array([dense[max(0, i - 4):i + 5].max() for i in range(len(dense))])
    k = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k /= k.sum()
    pad = np.pad(mx, 6, mode='edge')
    sm = np.maximum(np.convolve(pad, k, mode='valid'), 0)
    sm = np.maximum(sm, dense)                               # never below the measured need
    # key the corrected chain on every frame (the clips are keyed on every frame; keys are overwritten in place)
    curves = {(fc.data_path, fc.array_index): fc for layer in act.layers for strip in layer.strips
              for cb in strip.channelbags for fc in cb.fcurves}
    for i, f in enumerate(allf):
        if sm[i] <= 0.05:
            continue
        scene.frame_set(int(f))
        base = {n: rig.pose.bones[n].matrix_basis.copy() for n in CHAIN}
        rig.animation_data.action = None
        apply_tip(base, float(sm[i]))
        for n in CHAIN:
            q = rig.pose.bones[n].rotation_quaternion
            for c in range(4):
                fc = curves[(f'pose.bones["{n}"].rotation_quaternion', c)]
                kp = next((k for k in fc.keyframe_points if abs(k.co[0] - f) < 1e-3), None)
                if kp is None:
                    fc.keyframe_points.insert(float(f), q[c])
                else:
                    kp.co[1] = q[c]; kp.handle_left[1] = q[c]; kp.handle_right[1] = q[c]
        rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    fc.update()
    report[name] = {'max_tip_deg': round(float(sm.max()), 1), 'frames_corrected': int((sm > 0.05).sum()),
                    'frames': len(allf)}
    print('CLEARANCE', name, json.dumps(report[name]))
rig.animation_data.action = None
(P / 'work' / 'clearance.json').write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
