"""Meshy return: welded connected components (count, centroid, bbox) and a front/left render coloured by component.
Args: <glb> <out png prefix>"""
import bpy, bmesh, sys, json, colorsys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
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
rep = []
for r, k in enumerate(order):
    P = [bm.verts[i].co for i in comps[k]]
    c = sum(P, Vector()) / len(P)
    mn = [min(p[a] for p in P) for a in range(3)]; mx = [max(p[a] for p in P) for a in range(3)]
    rep.append({'rank': r, 'verts': len(P), 'centroid': [round(x, 3) for x in c], 'min': [round(x, 3) for x in mn],
                'max': [round(x, 3) for x in mx]})
me = bpy.data.meshes.new('m'); bm.to_mesh(me)
ob = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(ob)
col = me.color_attributes.new('c', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    r = rank[seen[v.index]]
    rgb = colorsys.hsv_to_rgb((r * 0.618) % 1, 0.8 if r else 0.15, 0.95)
    col.data[v.index].color = (*rgb, 1)
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.15
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, d in {'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)), 'top': Vector((0, 0.0001, 1))}.items():
    cam.location = d * 5
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('COMPS ' + json.dumps(rep))
