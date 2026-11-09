"""Clay shots of the head WITHOUT the hair shell (the largest-but-one head component), ears red, to locate Meshy's human
ears under the hair. Args (Blender): <blend> <out dir>"""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); os.makedirs(a[1], exist_ok=True)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
ear = np.zeros(len(me.polygons), np.int32)
if 'ear' in me.attributes: me.attributes['ear'].data.foreach_get('value', ear)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen, comps = set(), []
for f in bm.faces:
    if f.index in seen or not hd[f.index] or hn[f.index] or ear[f.index]: continue
    st, c = [f], []; seen.add(f.index)
    while st:
        g = st.pop(); c.append(g.index)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen and hd[h.index] and not hn[h.index] and not ear[h.index]:
                    seen.add(h.index); st.append(h)
    comps.append(c)
comps.sort(key=len, reverse=True)
hair = set(comps[1])
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in hair], context='FACES')
bm.to_mesh(me); bm.free()
me.materials.clear()
for name, col in (('b', (0.55, 0.55, 0.58, 1)), ('h', (0.8, 0.7, 0.62, 1)), ('e', (0.9, 0.2, 0.15, 1))):
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
ear = np.zeros(len(me.polygons), np.int32)
if 'ear' in me.attributes: me.attributes['ear'].data.foreach_get('value', ear)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.polygons.foreach_set('material_index', np.where(ear > 0, 2, np.where(hd > 0, 1, 0)).tolist())
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.35, 0.37)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 0.32
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((-0.011, 0.0, 0.80))
for k, d in {'px': (1, 0, 0.0), 'nx': (-1, 0, 0.0), 'front': (0, -1, 0), 'q': (1, -0.6, 0.2)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(a[1], f'skull_{k}.png'); bpy.ops.render.render(write_still=True)
print('SKULL', len(hair))
