"""Diagnostic renders of the source mouth: every separate piece in its own flat colour, two views, jaw open."""
import os, math, bmesh, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
o = bpy.data.objects['Wyrm']; rig = bpy.data.objects['Wyrm_Rig']
rig.animation_data.action = bpy.data.actions['Attack']; bpy.context.scene.frame_set(13)
me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; comp = []; seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen: seen.add(w.index); stack.append(w)
    comps.append(comp)
comps.sort(key=len, reverse=True)
colors = [(0.25, 0.4, 0.25), (1, 0, 0), (1, 0.5, 0), (0, 0.4, 1), (0, 1, 1), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0.5, 0, 1), (0, 1, 0)]
mats = []
for i, c in enumerate(colors):
    m = bpy.data.materials.new(f'P{i}'); m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (*c, 1)
    me.materials.append(m); mats.append(len(me.materials) - 1)
vpart = {}
for i, comp in enumerate(comps):
    for vi in comp: vpart[vi] = i
for p in me.polygons:
    p.material_index = mats[vpart[p.vertices[0]]]
scene = bpy.context.scene; scene.render.engine = 'BLENDER_EEVEE'; scene.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); scene.world = w; w.use_nodes = True
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 120
scene.render.resolution_x, scene.render.resolution_y = 800, 600
dg = bpy.context.evaluated_depsgraph_get()
ev = o.evaluated_get(dg).to_mesh()
head = [o.matrix_world @ ev.vertices[vi].co for i in (1, 2, 3, 4) for vi in comps[i]]
c = sum(head, Vector()) / len(head)
for name, off in (('front', Vector((0, -0.22, 0.03))), ('side', Vector((0.22, -0.02, 0.02))), ('below', Vector((0.05, -0.12, -0.15)))):
    cam.location = c + off
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, 'review', 'mouth', f'source_{name}.png')
    bpy.ops.render.render(write_still=True)
