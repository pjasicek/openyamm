"""Rock gate on work/anim_v4.blend: per clip, every second frame, queen vertices inside the posed rock.
Inside test: a ray from the vertex along -Y (toward the viewer, out of the niche) hits the rock an odd number of
times. Depth = distance to the first hit along -Y, i.e. how far forward that vertex would have to move to clear the
rock. Reports per clip the inside count, max depth (cm), its frame and the dominant bones of the worst vertices.
Death/Dead are reported but expected to touch (she sinks into the collapsing rock). Writes work/rock_gate.json."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; rock = bpy.data.objects['Rock']
scene = bpy.context.scene
gi = {g.index: g.name for g in queen.vertex_groups}
dom = [gi[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '' for v in queen.data.vertices]
# the abdomen tip rests in the niche on the lip by design: the lowest bone's vertices are not counted
skip = np.array([d == 'Abdomen1' for d in dom])
DIR = Vector((0, -1, 0))
report = {}
for name in ('Standing', 'Attack', 'Cast', 'Hit', 'Death'):
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    worst = {'inside_max': 0, 'depth_cm': 0.0, 'frame': None, 'bones': {}, 'frames_inside': 0}
    for f in range(f0, f1 + 1, 2 if name != 'Standing' else 6):
        scene.frame_set(f)
        deps = bpy.context.evaluated_depsgraph_get()
        rm = rock.evaluated_get(deps).to_mesh()
        bm = bmesh.new(); bm.from_mesh(rm); bm.transform(rock.matrix_world)
        tree = BVHTree.FromBMesh(bm); bm.free(); rock.evaluated_get(deps).to_mesh_clear()
        qm = queen.evaluated_get(deps).to_mesh()
        pc = [queen.matrix_world @ v.co for v in qm.vertices]
        queen.evaluated_get(deps).to_mesh_clear()
        depth = np.zeros(len(pc))
        for i, p in enumerate(pc):
            if skip[i]:
                continue
            o = p.copy(); hits = 0; first = None
            for _ in range(12):
                loc, nrm, idx, dist = tree.ray_cast(o, DIR, 50.0)
                if loc is None:
                    break
                hits += 1
                if first is None:
                    first = (loc - p).length
                o = loc + DIR * 1e-4
            if hits % 2 == 1:
                depth[i] = first
        n_in = int((depth > 0.01).sum())
        if n_in:
            worst['frames_inside'] += 1
        if depth.max() > worst['depth_cm'] / 100:
            top = np.argsort(-depth)[:40]
            bones = {}
            for i in top:
                if depth[i] > 0.01:
                    bones[dom[i]] = bones.get(dom[i], 0) + 1
            worst.update(depth_cm=round(float(depth.max()) * 100, 1), frame=f, bones=bones)
        worst['inside_max'] = max(worst['inside_max'], n_in)
    report[name] = worst
    print('ROCKGATE', name, json.dumps(worst))
(P / 'work' / 'rock_gate.json').write_text(json.dumps(report, indent=1))
