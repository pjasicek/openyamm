"""UV gate for work/step1_uv.blend: islands, atlas use, texel density (px/cm at 2048) per region vs its group median,
UV layout PNG coloured by region, region-coloured and checker renders of the model."""
import bpy, bmesh, sys, os, math, json, colorsys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_uv.blend'))
mesh = bpy.data.objects['Mage']; me = mesh.data
NAMES = json.loads(bpy.context.scene['pmn2_uv_regions'])
reg = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['uv_region'].data.foreach_get('value', reg)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
key = lambda l: (round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
island = [-1] * len(bm.faces); n = 0
for f in bm.faces:
    if island[f.index] >= 0: continue
    st = [f]; island[f.index] = n
    while st:
        g = st.pop()
        for e in g.edges:
            for o in e.link_faces:
                if o is g or island[o.index] >= 0: continue
                ua = {x.vert.index: key(x) for x in o.loops if x.vert in e.verts}
                ub = {x.vert.index: key(x) for x in g.loops if x.vert in e.verts}
                if ua == ub: island[o.index] = n; st.append(o)
    n += 1
def uv_area(f):
    pts = [l[uv].uv for l in f.loops]
    return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
def dens(fs):
    a3 = sum(f.calc_area() for f in fs); a2 = sum(uv_area(f) for f in fs)
    return math.sqrt(a2 * 2048 ** 2 / a3) / 100 if a3 else 0
out = {'islands': n, 'atlas_used_pct': round(100 * sum(uv_area(f) for f in bm.faces), 1), 'regions': {}}
for i, r in enumerate(NAMES):
    fs = [f for f in bm.faces if reg[f.index] == i]
    out['regions'][r] = {'faces': len(fs), 'px_per_cm': round(dens(fs), 2), 'islands': len({island[f.index] for f in fs})}
face = [f for f in bm.faces if NAMES[reg[f.index]] == 'Head' and f.calc_center_median().y < -0.03 and f.calc_center_median().z > 1.36]
out['face_px_per_cm'] = round(dens(face), 2)
# per-face stretch: ratio of uv/3d area relative to its region's value; report the worst 1% spread
st = {}
for i, r in enumerate(NAMES):
    fs = [f for f in bm.faces if reg[f.index] == i and f.calc_area() > 1e-8]
    if not fs: continue
    k = np.array([math.sqrt(uv_area(f) / f.calc_area()) for f in fs]); k /= np.median(k)
    st[r] = [round(float(np.percentile(k, 2)), 2), round(float(np.percentile(k, 98)), 2)]
out['stretch_p2_p98'] = st
print('UVCHECK', json.dumps(out))
json.dump(out, open(os.path.join(common.WORK, 'uv_check.json'), 'w'), indent=1)
# layout polygons for drawing outside Blender (tools/draw_uv_layout.py)
json.dump({'regions': NAMES, 'faces': [[int(reg[f.index]), [[round(l[uv].uv.x, 5), round(l[uv].uv.y, 5)] for l in f.loops]]
                                        for f in bm.faces]}, open(os.path.join(common.WORK, 'uv_layout.json'), 'w'))
cols = [tuple(int(255 * c) for c in colorsys.hsv_to_rgb((i * 0.618) % 1, 0.6, 0.95)) for i in range(len(NAMES))]
bm.free()
# region colours as material slots, then checker
for i, r in enumerate(NAMES):
    m = bpy.data.materials.new(r); m.diffuse_color = tuple(c / 255 for c in cols[i]) + (1,); me.materials.append(m)
me.polygons.foreach_set('material_index', reg)
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, 'uvreg'), 0.8, 1.7, views=('front', 'three_quarter', 'back'), resolution=(500, 750))
me.materials.clear()
mat = bpy.data.materials.new('checker'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.new('chk', 1024, 1024); tex.image.generated_type = 'UV_GRID'
tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); me.materials.append(mat)
common.workbench_clay(sc, textured=True)
common.render_views(os.path.join(common.REVIEW, 'uvchk'), 0.8, 1.7, views=('front', 'three_quarter', 'back'), resolution=(500, 750))
common.render_views(os.path.join(common.REVIEW, 'uvchk_head'), 1.43, 0.36, views=('front', 'three_quarter'), resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, 'uvchk_hand'), 0.82, 0.16, views=('front', 'right'), resolution=(350, 350), target=(-0.43, -0.02))
