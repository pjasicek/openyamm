"""See-through holes of a reduction: ray grids from 16 cameras (8 azimuths x eye heights 1.0 / 1.6 m, 2 m away, 3 mm
spacing) against the reduced Body (<blend>, rest pose). A ray whose first hit is the BACK of a skin face looks into the
closed body through a hole (h65: a decimation fold opened the chest under the necklace pendants). The installed master
(../mm6_natm_claude/work/rig_v6.blend) is probed the same way as the baseline. Hits are clustered (3 cm).
Args: -- [<blend>]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
blend = a[0] if a else 'work/rig_v6.blend'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def probe(path):
    bpy.ops.wm.open_mainfile(filepath=path); me = bpy.data.objects['Body'].data
    g = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', g)
    fskin = np.array([g[p.vertices[0]] == 0 for p in me.polygons])
    if 'fgarment' in me.attributes:
        fg = np.zeros(len(me.polygons), np.int32); me.attributes['fgarment'].data.foreach_get('value', fg); fskin = fg == 0
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
    bad = []
    for az in range(8):
        for eye in (1.0, 1.6):
            ang = az * math.pi / 4; cam = Vector((2 * math.sin(ang), -2 * math.cos(ang), eye))
            for gx in np.arange(-0.6, 0.6, 0.003):
                for gz in np.arange(0.0, 1.75, 0.003):
                    d = (Vector((gx * math.cos(ang), gx * math.sin(ang), gz)) - cam).normalized()
                    loc, n, i, dist = bvh.ray_cast(cam, d, 4.0)
                    if loc is not None and fskin[i] and n.dot(d) > 0.2:
                        bad.append(np.array(loc))
    return np.array(bad)


def report(tag, bad):
    print('HOLES', tag, 'backface skin hits', len(bad))
    done = np.zeros(len(bad), bool); out = []
    for i in range(len(bad)):
        if done[i]: continue
        m = np.linalg.norm(bad - bad[i], axis=1) < 0.03; done |= m
        if m.sum() >= 5: out.append((int(m.sum()), np.round(bad[m].mean(0), 3).tolist()))
    for k, c in sorted(out, reverse=True)[:12]: print('HOLE', tag, k, c)


report('installed', probe(os.path.join(HERE, '..', 'mm6_natm_claude', 'work', 'rig_v6.blend')))
report('reduced', probe(os.path.join(HERE, blend)))
