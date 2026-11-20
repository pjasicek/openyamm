"""Probe head geometry of a work blend: head bones, connected parts with their dominant bones, lip faces.
Args: -- <blend>"""
import bpy, sys, bmesh
import numpy as np
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects.get('Body') or bpy.data.objects.get('DragonKing')
print('objects', [(o.name, o.type) for o in bpy.data.objects])
me = body.data
print('mesh', len(me.vertices), len(me.polygons), 'uv', [l.name for l in me.uv_layers], 'attrs',
      [a.name for a in me.attributes if not a.name.startswith('.')], 'mats', [m.name for m in me.materials])
HEADB = ['Xneckpiv', 'XneckA', 'XneckB', 'XneckC', 'XneckD', 'Bip01 Head', 'Xheadpiv', 'Xhead', 'Xjawbase', 'Xjawpivot',
         'Xjaw', 'Xtong', 'Xtongpiv', 'Xtopfinpiv', 'Xfinpiv', 'Xchinfinpiv', 'Xbotfinpiv']
for b in rig.data.bones:
    if any(k in b.name for k in ('head', 'Head', 'jaw', 'Jaw', 'tong', 'fin', 'neck', 'Neck', 'horn', 'Horn')):
        print('BONE', b.name, 'parent', b.parent.name if b.parent else None, 'head', np.round(tuple(rig.matrix_world @ b.head_local), 3),
              'tail', np.round(tuple(rig.matrix_world @ b.tail_local), 3))
vg = {g.index: g.name for g in body.vertex_groups}
dom = [vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(me.vertices), int); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
fcomp = np.array([comp[p.vertices[0]] for p in me.polygons])
headish = set(['Xheadpiv', 'Xhead', 'Xjawbase', 'Xjawpivot', 'Xjaw', 'Xtong', 'Xtongpiv', 'Bip01 Head'])
for k in range(cid):
    m = comp == k
    c = Counter(dom[i] for i in np.nonzero(m)[0])
    top = c.most_common(3)
    if any(t[0] in headish or 'fin' in t[0] for t in top) or m.sum() > 2000:
        print('PART', k, 'verts', int(m.sum()), 'faces', int((fcomp == k).sum()), 'lo', CO[m].min(0).round(3), 'hi', CO[m].max(0).round(3), top)
if 'lip' in me.attributes:
    lip = np.zeros(len(me.polygons), bool); me.attributes['lip'].data.foreach_get('value', lip)
    lv = np.unique(np.concatenate([list(me.polygons[i].vertices) for i in np.nonzero(lip)[0]]))
    print('LIP faces', int(lip.sum()), 'parts', Counter(fcomp[lip]).most_common(4), 'lo', CO[lv].min(0).round(3), 'hi', CO[lv].max(0).round(3))
c = Counter(dom)
print('DOMINANT head bones', {k: c[k] for k in c if k in headish or 'fin' in k or 'neck' in k.lower()})
