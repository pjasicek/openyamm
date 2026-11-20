"""Mark the body's ivory parts (spurs, claws, horns, teeth) by their base colour: per vertex the mean base-colour texel
of its loops (the material's base-colour image); ivory = bright and unsaturated, grown two edge rings (the spur roots). Attribute 'ivory' (INT 0/1), used by
make_carapace.py to project plates onto the skin only. Saves in place. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data
imgs = {}
for k, m in enumerate(me.materials):
    tex = next(n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links))
    im = tex.image; w, h = im.size
    imgs[k] = (np.array(im.pixels[:]).reshape(h, w, 4)[..., :3], w, h)
uv = me.uv_layers.active.data
acc = np.zeros((len(me.vertices), 3)); cnt = np.zeros(len(me.vertices))
for p in me.polygons:
    px, w, h = imgs[p.material_index]
    for li, vi in zip(p.loop_indices, p.vertices):
        u, v = uv[li].uv
        x = int(np.clip(u % 1.0, 0, 0.9999) * w); y = int(np.clip(v % 1.0, 0, 0.9999) * h)
        acc[vi] += px[y, x]; cnt[vi] += 1
col = acc / np.maximum(cnt, 1)[:, None]
mx, mn = col.max(1), col.min(1)
sat = (mx - mn) / np.maximum(mx, 1e-6)
ivory = ((mx > 0.45) & (sat < 0.45)).astype(np.int32)
core = int(ivory.sum())
RINGS = 2                                       # the spur roots: grow the mask two edge rings into the skin
E = np.array([tuple(e.vertices) for e in me.edges])
for _ in range(RINGS):
    grow = ivory.copy()
    grow[E[:, 0][ivory[E[:, 1]] == 1]] = 1; grow[E[:, 1][ivory[E[:, 0]] == 1]] = 1
    ivory = grow
att = me.attributes.get('ivory') or me.attributes.new('ivory', 'INT', 'POINT')
att.data.foreach_set('value', ivory.tolist())
print('IVORY', core, 'grown', int(ivory.sum()), 'of', len(ivory))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[0]))
sys.stdout.flush(); os._exit(0)
