"""Job 7: clay close-ups of the ears on a master blend (rest pose, master frame): views R/L side, low 3/4 R/L from below
the chin, 3/4 back R/L; hair shown or hidden (`nohair` deletes every loose part above the shoulders but the skin and
the ears). Writes <out>_<view>.png (600 px). Args: <blend> <out prefix> [hair|nohair] [views]"""
import bpy, bmesh, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]; mode = a[2] if len(a) > 2 else 'hair'
views = (a[3] if len(a) > 3 else 'R,L,lowR,lowL,backR,backL').split(',')
ob = bpy.data.objects['Body']; rig = ob.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
me = ob.data
if mode == 'nohair':
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    le = bm.faces.layers.int.get('ear'); lh = bm.faces.layers.int['head']
    comp = {}; parts = []
    for v in bm.verts:
        if v in comp: continue
        st = [v]; comp[v] = len(parts); cur = [v]
        while st:
            x = st.pop()
            for e in x.link_edges:
                o = e.other_vert(x)
                if o not in comp: comp[o] = len(parts); st.append(o); cur.append(o)
        parts.append(cur)
    big = max(range(len(parts)), key=lambda i: len(parts[i]))
    kill = [v for i, p in enumerate(parts) if i != big and not (le and any(f[le] for f in p[0].link_faces))
            and sum(v.co.z for v in p) / len(p) > 0.3 for v in p]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(me); me.update()
m = bpy.data.materials.new('clay'); m.use_nodes = True
bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Base Color'].default_value = (0.62, 0.55, 0.5, 1)
bs.inputs['Roughness'].default_value = 0.6
me.materials.clear(); me.materials.append(m)
for p in me.polygons: p.material_index = 0
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o)
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Color'].default_value = (0.25, 0.27, 0.3, 1)
for nm, rot, en in (('key', (45, 0, 40), 3.0), ('key2', (45, 0, -40), 2.0), ('fill', (110, 0, 180), 0.8)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cd.lens = 60; cd.clip_start = 0.01
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for v in views:
    s = -1 if v.endswith('L') else 1
    if v in ('R', 'L'): tgt = Vector((s * 0.06, -0.02, 0.41)); d = Vector((s, 0, 0)); dist = 0.28
    elif v.startswith('low'): tgt = Vector((s * 0.04, -0.03, 0.40)); d = Vector((s * 0.7, -0.6, -0.4)); dist = 0.3
    else: tgt = Vector((s * 0.05, 0.0, 0.41)); d = Vector((s * 0.7, 0.7, 0.1)); dist = 0.3
    cam.location = tgt + d.normalized() * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
print('EARCLAY', out)
