"""Per-piece collapse reduction toward ~10k triangles. Every piece is rigid, so pieces are reduced separately
(loose-part split, decimate by class target, rejoin); groups, the piece attribute and materials survive.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Skeleton']
before = sum(len(p.vertices) - 2 for p in body.data.polygons)

TARGET = {0: 1500, 2: 520, 4: 260, 5: 260, 2000: 1850, 2001: 380}
CLASS = {
    'long': ([8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 23, 25], 120),
    'vertebra': ([7, 14, 15, 20, 21, 22, 27, 30], 90),
    'girdle': ([24, 28, 33, 34], 90),
    'ball': ([37, 40, 53, 61], 50),
}
for ids, t in CLASS.values():
    for i in ids:
        TARGET[i] = t


def target(pid, n, shells):
    if pid in TARGET:
        return TARGET[pid]
    if pid in (2002, 2003):
        return 28 * shells            # per tooth shell (12 per row collapsed them into spikes)
    if pid == 999:
        return n                      # sword (authored low poly)
    return max(24, int(n * 0.5))      # hand and toe pieces


for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
pieces = [o for o in bpy.data.objects if o.type == 'MESH']
# a piece may be several loose shells: share its target between them by size
by_pid = {}
for o in pieces:
    pid = int(o.data.attributes['piece'].data[0].value)
    by_pid.setdefault(pid, []).append(o)
report = {}
for pid, objs in by_pid.items():
    ns = [sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs]
    tot = sum(ns)
    tgt = target(pid, tot, len(objs))
    for o, n in zip(objs, ns):
        want = tgt * n / tot
        if want < n * 0.97:
            m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = max(want / n, 0.05)
            bpy.context.view_layer.objects.active = o
            for x in bpy.data.objects:
                x.select_set(x == o)
            bpy.ops.object.modifier_apply(modifier='dec')
    report[pid] = (tot, sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs))
for x in bpy.data.objects:
    x.select_set(x.type == 'MESH')
keep = next(o for o in pieces if o.name == 'Skeleton') if any(o.name == 'Skeleton' for o in pieces) else pieces[0]
bpy.context.view_layer.objects.active = keep
bpy.ops.object.join()
keep.name = keep.data.name = 'Skeleton'
after = sum(len(p.vertices) - 2 for p in keep.data.polygons)
for pid in sorted(report):
    a, b = report[pid]
    if a != b:
        print('PIECE', pid, a, '->', b)
print('TRIS', before, '->', after)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
