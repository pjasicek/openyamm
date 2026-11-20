"""Triangle budget on work/step2.blend: the head-only Smart Topology came back at 15k triangles for the head alone.
Decimate the head part (face attribute part = 1) to HEAD_TRIANGLES and the body to BODY_TRIANGLES, each with a
collapse restricted to its own vertices (the seam band between them is held fixed by both). Hands and claws are
protected: vertices farther than 0.4 m from the body axis keep their density. Writes work/step3.blend and reports."""
import bpy, json, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
HEAD_TRIANGLES = 5000
BODY_TRIANGLES = 7200
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step2.blend'))
ob = bpy.data.objects['Queen']
me = ob.data
part = np.array([v.value for v in me.attributes['part'].data])
faces = [np.array(p.vertices) for p in me.polygons]
tri = np.array([len(f) - 2 for f in faces])
cut = json.loads((P / 'work' / 'graft_report.json').read_text())['cut_z']
co = np.array([tuple(v.co) for v in me.vertices])
report = {'before': {'head': int(tri[part == 1].sum()), 'body': int(tri[part == 0].sum())}}
bpy.context.view_layer.objects.active = ob
for which, target in ((1, HEAD_TRIANGLES), (0, BODY_TRIANGLES)):
    tri_now = sum(len(p.vertices) - 2 for p in me.polygons)
    part = np.array([v.value for v in me.attributes['part'].data])
    verts = set()
    for p in me.polygons:
        if part[p.index] == which:
            verts.update(p.vertices)
    co = np.array([tuple(v.co) for v in me.vertices])
    g = ob.vertex_groups.new(name=f'reduce{which}')
    keep_far = np.hypot(co[:, 0], co[:, 1] + 0.2) > 0.4 if which == 0 else np.zeros(len(co), bool)
    seam = np.abs(co[:, 2] - cut) < 0.07
    ids = [i for i in verts if not keep_far[i] and not seam[i]]
    g.add(ids, 1.0, 'REPLACE')
    own = sum(len(p.vertices) - 2 for p in me.polygons if part[p.index] == which)
    mod = ob.modifiers.new('dec', 'DECIMATE')
    mod.vertex_group = g.name
    mod.use_collapse_triangulate = True
    mod.ratio = max(0.05, 1.0 - (own - target) / tri_now)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.vertex_groups.remove(ob.vertex_groups[g.name])
part = np.array([v.value for v in me.attributes['part'].data])
tri = np.array([len(p.vertices) - 2 for p in me.polygons])
report['after'] = {'head': int(tri[part == 1].sum()), 'body': int(tri[part == 0].sum()), 'total': int(tri.sum())}
print('REDUCE', json.dumps(report))
(P / 'work' / 'reduce_report.json').write_text(json.dumps(report, indent=1))
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(str(P / 'review' / 'reduce_head'), 1.98, 0.75, views=('front', 'three_quarter', 'left'),
                    resolution=(600, 600))
common.render_views(str(P / 'review' / 'reduce_body'), 1.2, 2.6, views=('front', 'left'), resolution=(500, 750))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'step3.blend'))
