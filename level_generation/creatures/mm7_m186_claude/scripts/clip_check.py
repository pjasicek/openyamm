"""Clip sheet (front + three-quarter at 5 frames per clip) and per-frame floor report for a bat animation blend.
Args: <blend> <out tag>. Writes review/clips_<tag>.png and review/clips_<tag>.json (min z of the whole mesh and of the
body per frame; max z)."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, tag = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, src))
import common_render as C
rig = bpy.data.objects['Dragonfly_Rig']; mesh = bpy.data.objects['Dragonfly']; sc = bpy.context.scene
vg = {g.index: g.name for g in mesh.vertex_groups}
dom = [vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices]
body = np.array(['Wing' not in n for n in dom])
def co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); ev.to_mesh_clear(); return a.reshape(-1, 3)
report, cells = {}, []
clips = [a.name for a in bpy.data.actions if a.name in ('Fly', 'Attack', 'Hit', 'Death', 'Dead', 'Cast')]
clips.sort(key=['Fly', 'Attack', 'Cast', 'Hit', 'Death', 'Dead'].index)
os.makedirs(os.path.join(HERE, f'review/clips_{tag}'), exist_ok=True)
for c in clips:
    rig.animation_data.action = bpy.data.actions[c]
    f0, f1 = (int(x) for x in bpy.data.actions[c].frame_range)
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); p = co()
        rows.append([f, round(float(p[:, 2].min()), 4), round(float(p[body, 2].min()), 4), round(float(p[:, 2].max()), 4)])
    report[c] = {'frames': f1 - f0, 'min_z': min(r[1] for r in rows), 'body_min_z': min(r[2] for r in rows),
                 'max_z': max(r[3] for r in rows), 'last': rows[-1], 'rows': rows}
    for k in range(5):
        f = f0 + round((f1 - f0) * k / 4); sc.frame_set(f)
        for view, loc in (('s', (-1.6, 0.0, 0.25)), ('q', (-1.0, -1.1, 0.75))):
            p = os.path.join(HERE, f'review/clips_{tag}/{c}_{k}_{view}.png')
            C.render_ortho(loc, (0, 0, 0.2), 1.1, p, res=(320, 240), mesh_name='Dragonfly', rig_name='Dragonfly_Rig'); cells.append(p)
json.dump(report, open(os.path.join(HERE, f'review/clips_{tag}.json'), 'w'), indent=1)
C.sheet(os.path.join(HERE, f'review/clips_{tag}.png'), cells, 10)
print('CLIPS', {c: (r['min_z'], r['body_min_z'], r['max_z'], r['last'][1:]) for c, r in report.items()})
