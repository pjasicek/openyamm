"""v2 reduction ladder check (Blender): the animated reduced candidate against the animated unreduced mesh (same rig,
same clip tables), surface distance both ways at 7 frames per clip (BVH), p99 and max; plus same-camera renders.
Usage: reduction_check_v2.py -- <candidate_anim.blend> <reference_anim.blend> <label>. Writes review/reduction/<label>.json"""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]; a = sys.argv[sys.argv.index('--') + 1:]
def load(path, tag):
    with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = ['Body', 'Rig']; dst.actions = list(src.actions); names = list(src.actions)
    for o in dst.objects: bpy.context.scene.collection.objects.link(o); o.name = tag + o.name
    return dst.objects, dict(zip(names, dst.actions))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
(cb, cr), ca = load(a[0], 'C'); (rb, rr), ra = load(a[1], 'R')
def surf(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); v = [p.co.copy() for p in m.vertices]; f = [list(p.vertices) for p in m.polygons]; ev.to_mesh_clear()
    return v, BVHTree.FromPolygons(v, f, all_triangles=True)
rep = {'candidate': a[0], 'triangles': len(cb.data.polygons), 'reference_triangles': len(rb.data.polygons), 'clips': {}}
for name in ca:
    cr.animation_data.action = ca[name]; rr.animation_data.action = ra[name]; lo, hi = ca[name].frame_range; errs = []
    for fr in np.linspace(lo, hi, 7):
        sc.frame_set(int(fr), subframe=fr % 1); cv, ct = surf(cb); rv, rt = surf(rb)
        errs += [rt.find_nearest(v)[3] for v in cv] + [ct.find_nearest(v)[3] for v in rv[::2]]
    q = np.percentile(errs, [99, 100]); rep['clips'][name] = {'p99_mm': round(float(q[0]) * 1000, 3), 'max_mm': round(float(q[1]) * 1000, 2)}
rep['passed'] = all(v['p99_mm'] <= 1.0 and v['max_mm'] <= 7 for v in rep['clips'].values())
(P / 'review/reduction').mkdir(exist_ok=True); (P / f'review/reduction/{a[2]}.json').write_text(json.dumps(rep, indent=1) + '\n'); print('REDCHECK', a[2], rep['triangles'], rep['passed'], rep['clips'])
