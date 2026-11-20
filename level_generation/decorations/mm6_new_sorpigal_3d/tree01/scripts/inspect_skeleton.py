import bpy, sys, json
P = json.loads(sys.argv[sys.argv.index('--') + 1])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **P)
t = bpy.data.objects['tree']; cu = t.data
print('CURVE bevel_depth', cu.bevel_depth, 'bevel_res', cu.bevel_resolution, 'res_u', cu.resolution_u, 'splines', len(cu.splines), 'scale', tuple(t.scale), 'loc', tuple(t.location))
import collections
th = []
for s in cu.splines:
    pts = s.bezier_points
    th.append((max(p.radius for p in pts) * cu.bevel_depth, len(pts), pts[0].co.z))
th.sort(reverse=True)
print('THICKEST', [(round(a, 3), b, round(c, 2)) for a, b, c in th[:12]])
bins = collections.Counter(round(a, 2) for a, _, _ in th); print('THICKNESS hist', sorted(bins.items(), reverse=True)[:25])
