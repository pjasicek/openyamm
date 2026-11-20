"""UV islands per uv_region of work/step1_uv.blend (count, faces in islands of < 4 faces). Args: [blend]."""
import bpy, bmesh, sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv
                                               else 'step1_uv.blend'))
me = bpy.data.objects['Titan'].data; names = json.loads(bpy.context.scene['ttn_uv_regions'])
reg = [0] * len(me.polygons); me.attributes['uv_region'].data.foreach_get('value', reg)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
key = lambda l: (round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
seen = set(); stats = collections.defaultdict(lambda: [0, 0])
for f in bm.faces:
    if f.index in seen:
        continue
    st = [f]; seen.add(f.index); n = 0
    while st:
        g = st.pop(); n += 1
        for l in g.loops:
            e = l.edge
            for h in e.link_faces:
                if h.index in seen or h is g:
                    continue
                # shared edge with identical UVs on both sides
                lh = next(x for x in h.loops if x.edge == e)
                if {key(l), key(l.link_loop_next)} == {key(lh), key(lh.link_loop_next)}:
                    seen.add(h.index); st.append(h)
    s = stats[names[reg[f.index]]]; s[0] += 1; s[1] += n if n < 4 else 0
print('ISLANDS', sum(v[0] for v in stats.values()), dict(stats))
