"""Render the head with each HeadUV chart in its own colour (front, 3/4, side): where the seams cross the face.
Args (Blender): <blend> <uv layer> <out prefix>"""
import bpy, bmesh, sys, random
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uv = bm.loops.layers.uv[a[1]]
lab = [-1] * len(bm.faces); k = 0
def key(l):
    return (round(l[uv].uv.x, 5), round(l[uv].uv.y, 5))
for f in bm.faces:
    if lab[f.index] >= 0:
        continue
    st = [f]; lab[f.index] = k
    while st:
        g = st.pop()
        for l in g.loops:
            e = l.edge
            for h in e.link_faces:
                if lab[h.index] >= 0:
                    continue
                # same chart if the shared edge has the same UVs on both faces
                la = [x for x in g.loops if x.edge == e][0]; lb = [x for x in h.loops if x.edge == e][0]
                ka = {key(la), key(la.link_loop_next)}; kb = {key(lb), key(lb.link_loop_next)}
                if ka == kb:
                    lab[h.index] = k; st.append(h)
    k += 1
random.seed(3)
mats = []
for i in range(k):
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = (random.random(), random.random(), random.random(), 1); mats.append(m)
me.materials.clear()
for m in mats:
    me.materials.append(m)
for p in me.polygons:
    p.material_index = lab[p.index]
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'; sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.32
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0.01, 0.72))
for nm, d in (('front', (0, -1, 0)), ('q34', (-1, -1.2, 0.2)), ('side', (-1, 0, 0)), ('below', (0, -0.7, -1))):
    cam.location = c + Vector(d).normalized() * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{nm}.png'; bpy.ops.render.render(write_still=True)
print('CHARTS', k)
