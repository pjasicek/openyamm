"""G4 probe on work/rig_v1.blend: dominant-bone colour render and extreme poses (arms up and out, elbows 100 deg,
wrist bend, finger curl, spine twist, abdomen bend, head turn). Each pose also reports the worst edge stretch
(deformed length / rest length) per dominant bone. Writes review/stress_<pose>_<view>.png and work/stress.json."""
import bpy, sys, json, math, colorsys
import numpy as np
from pathlib import Path
from mathutils import Euler, Quaternion
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rig_v1.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; rock = bpy.data.objects['Rock']
rock.hide_render = True
me = queen.data
NV = len(me.vertices)
gi = {g.index: g.name for g in queen.vertex_groups}
dom = []
for v in me.vertices:
    best = max(v.groups, key=lambda g: g.weight) if len(v.groups) else None
    dom.append(gi[best.group] if best else '')
names = sorted(set(dom))
rng = np.random.default_rng(7)
colour = {n: colorsys.hsv_to_rgb(rng.random(), 0.75, 0.95) for n in names}
ca = me.color_attributes.new('dom', 'BYTE_COLOR', 'POINT')
for i, n in enumerate(dom):
    ca.data[i].color = (*colour[n], 1.0)
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices])
rest_len = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
OK = rest_len > 0.005                  # slivers from decimation and the graft tuck: their ratio means nothing
PLACE = (lambda d: d.get('queen_actor_location', d['queen_location']))(json.loads((P / 'work' / 'placement.json').read_text()))
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'VERTEX'
focus = {'z': 1.95, 'h': 2.8}


def rot(n, x=0, y=0, z=0):
    pb = rig.pose.bones[n]; pb.rotation_mode = 'XYZ'
    pb.rotation_euler = Euler((math.radians(x), math.radians(y), math.radians(z)))


POSES = {
    'rest': {},
    'arms_up': {'B_L_UpperArm': (0, 0, -95), 'B_R_UpperArm': (0, 0, 95), 'B_L_Clavicle': (0, 0, -15),
                'B_R_Clavicle': (0, 0, 15)},
    'elbows': {'B_L_Forearm': (0, 0, -100), 'B_R_Forearm': (0, 0, 100), 'B_L_UpperArm': (-40, 0, 0),
               'B_R_UpperArm': (-40, 0, 0)},
    'wrists_fingers': {'B_L_Hand': (0, 0, -50), 'B_R_Hand': (0, 0, 50),
                       **{f'B_{s}_Finger{i}{k}': (0, 0, (-50 if s == 'L' else 50)) for s in 'LR' for i in range(1, 5)
                          for k in ('', '1', '2')}},
    'twist': {'B_Spine': (0, 15, 0), 'B_Spine1': (0, 15, 0), 'B_Spine2': (0, 15, 0), 'B_Neck': (0, 20, 0),
              'B_Head': (20, 25, 0)},
    'abdomen': {f'Abdomen{i}': (8, 0, 6) for i in range(1, 7)},
}
report = {}
deps = bpy.context.evaluated_depsgraph_get()
for pose, rots in POSES.items():
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    for n, (x, y, z) in rots.items():
        if n in rig.pose.bones:
            rot(n, x, y, z)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    em = queen.evaluated_get(deps).to_mesh()
    pc = np.array([tuple(v.co) for v in em.vertices])
    queen.evaluated_get(deps).to_mesh_clear()
    L = np.linalg.norm(pc[E[:, 0]] - pc[E[:, 1]], axis=1)
    ratio = np.maximum(L / np.maximum(rest_len, 1e-6), np.maximum(rest_len, 1e-6) / np.maximum(L, 1e-6))
    ratio[~OK] = 1.0
    by = {}
    for k in np.argsort(-ratio)[:200]:
        n = dom[E[k, 0]]
        by[n] = max(by.get(n, 0.0), float(ratio[k]))
    worst = int(np.argmax(ratio))
    wv = {}
    for k in np.argsort(-ratio)[:3]:
        for vi in E[k]:
            v = me.vertices[int(vi)]
            wv[int(vi)] = {'co': [round(x, 3) for x in v.co], 'ratio': round(float(ratio[k]), 2),
                           'weights': {gi[g.group]: round(g.weight, 2) for g in v.groups if g.weight > 0.05}}
    report[pose] = {'max_stretch': round(float(ratio.max()), 2), 'p99': round(float(np.percentile(ratio, 99)), 2),
                    'worst_edge_bones': [dom[E[worst, 0]], dom[E[worst, 1]]],
                    'by_bone_top': dict(sorted(by.items(), key=lambda kv: -kv[1])[:6]), 'worst_vertices': wv}
    print('STRESS', pose, json.dumps(report[pose]))
    for view in ('front', 'left'):
        common.render_views(str(P / 'review' / f'stress_{pose}'), PLACE[2] + 1.25, 2.9, views=(view,),
                            resolution=(500, 650), target=(PLACE[0], PLACE[1]))
(P / 'work' / 'stress.json').write_text(json.dumps(report, indent=1))
