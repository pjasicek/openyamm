"""Faces whose vertices are dominated by bones of different chains that move apart (tail vs hind leg), i.e. surface
bridges Meshy fused between separate body parts. Prints count and location. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
b = bpy.data.objects['Body']; me = b.data; vn = [g.name for g in b.vertex_groups]
dom = [vn[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices]
fam = lambda n: 'tail' if n.startswith('Tail') else ('legL' if n.endswith('_L') and n[0] in 'TSH' else 'legR' if n.endswith('_R') and n[0] in 'TSH' else 'other')
bad = [p for p in me.polygons if {'tail', 'legL'} <= {fam(dom[i]) for i in p.vertices} or {'tail', 'legR'} <= {fam(dom[i]) for i in p.vertices}]
co = np.array([tuple(me.vertices[i].co) for p in bad for i in p.vertices]) if bad else np.zeros((0, 3))
print('BRIDGE faces', len(bad), 'centre', np.round(co.mean(0), 3) if len(co) else None, 'bounds', np.round(co.min(0), 3) if len(co) else None, np.round(co.max(0), 3) if len(co) else None)
