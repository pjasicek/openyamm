"""Render a GLB's welded connected components in distinct colours (top, bottom, left, front) and print them.
Args: glb outdir prefix"""
import bpy, bmesh, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
src = next(o for o in sc.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
seen = {}; comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = len(comps); st.append(y)
    comps.append(c)
order = sorted(range(len(comps)), key=lambda k: -len(comps[k]))
rank = {k: r for r, k in enumerate(order)}
pal = [(.9, .9, .9), (.6, .6, .6), (1, .2, .2), (.2, 1, .2), (.2, .4, 1), (1, 1, .2), (1, .2, 1), (.2, 1, 1),
       (1, .6, .1), (.6, .3, 1), (.5, 1, .6), (1, .5, .6), (.4, .2, .1), (.1, .4, .2)]
for r, k in enumerate(order):
    pts = [bm.verts[i].co for i in comps[k]]
    cen = sum(pts, Vector()) / len(pts)
    print('COMP', r, len(comps[k]), [round(x, 3) for x in cen], pal[r % len(pal)])
me = bpy.data.meshes.new('c'); bm.to_mesh(me)
ob = bpy.data.objects.new('c', me); sc.collection.objects.link(ob)
for o in list(sc.objects):
    if o is not ob and o.type == 'MESH':
        o.hide_render = True
col = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    col.data[v.index].color = (*pal[rank[seen[v.index]] % len(pal)], 1)
me.color_attributes.active_color = col
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 512
lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)]); hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
c = (lo + hi) / 2
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = max(hi - lo) * 1.1; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(outdir, exist_ok=True)
for v, dv in {'top': (0, 0.0001, 1), 'bottom': (0, 0.0001, -1), 'left': (1, 0, 0), 'front': (0, -1, 0)}.items():
    dv = Vector(dv).normalized()
    cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
