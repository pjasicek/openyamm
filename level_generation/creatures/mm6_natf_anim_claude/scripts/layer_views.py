"""Rest-pose renders with the separate skirt panel (welded part of PANEL_SIZE faces) in red and the rest of the body
grey, solid shading, backface culling. Usage: blender -b -P layer_views.py -- <blend> <out prefix> [Action:frame]
(blue: body skin under the skirt, i.e. faces below the waist without swing-helper weights)"""
import os, sys, bpy, bmesh
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if len(a) > 2:
    act = bpy.data.actions[a[2].split(':')[0]]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(a[2].split(':')[1]))
else:
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.faces.ensure_lookup_table()
seen = set(); red = set()
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; comp = []; seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.edges:
            for o in e.link_faces:
                if o.index not in seen: seen.add(o.index); st.append(o)
    if len(comp) == int(os.environ.get('PANEL_SIZE', '524')): red |= set(comp)
# remove_doubles keeps face order for faces (no faces merged), so indices map to the mesh
m_grey = bpy.data.materials.new('G'); m_grey.diffuse_color = (.7, .7, .7, 1)
m_red = bpy.data.materials.new('R'); m_red.diffuse_color = (.85, .15, .1, 1)
m_blue = bpy.data.materials.new('B'); m_blue.diffuse_color = (.1, .3, .9, 1)
me.materials.clear(); me.materials.append(m_grey); me.materials.append(m_red); me.materials.append(m_blue)
names = {g.index: g.name for g in body.vertex_groups}
def skirtw(v): return sum(x.weight for x in v.groups if names[x.group] in ('B_L_ThighSwing', 'B_R_ThighSwing')) > 0 or v.co.z > 0.93
for p in me.polygons:
    vz = [me.vertices[i] for i in p.vertices]
    under = all(v.co.z < 0.95 for v in vz) and not any(sum(x.weight for x in v.groups if names[x.group] in ('B_L_ThighSwing','B_R_ThighSwing')) > 0 for v in vz)
    p.material_index = 1 if p.index in red else (2 if under else 0)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
for o in bpy.data.objects:
    if o.name in ('ForearmBlade', 'LeafShield'): o.hide_render = True
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .75
for v, d in (('front', (0, -1, .05)), ('back', (0, 1, .05)), ('right', (-1, 0, .05)), ('left', (1, 0, .05))):
    c = Vector((0, 0, .75)); cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
