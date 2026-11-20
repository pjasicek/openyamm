"""Workbench renders of work/source.blend coloured by the decimation plan (kept grey; per category colour, lighter for
higher ratios): review/groups/<view>.png. Usage: blender -b -P render_groups.py"""
import os, json, colorsys, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data
groups = np.load(os.path.join(HERE, 'work', 'groups.npy')); plan = json.load(open(os.path.join(HERE, 'work', 'group_plan.json')))
me.calc_loop_triangles()
assert len(me.loop_triangles) == len(groups) == len(me.polygons)
HUE = dict(hand=.0, foot=.08, limb=.15, torso=.33, sheet=.55, dome=.75)
col = me.color_attributes.new('Plan', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    g = int(groups[p.index])
    if g == 0:
        c = (.55, .55, .55, 1)
    else:
        r, cat, _ = plan[str(g)]
        c = (*colorsys.hsv_to_rgb(HUE[cat], .8, .45 + .5 * (1 - r) + .1 * (g % 3)), 1)
    for li in p.loop_indices:
        col.data[li].color = c
me.color_attributes.active_color = col; me.color_attributes.render_color_index = me.color_attributes.active_color_index
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o is not src
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
src.data.materials.clear() if False else None
sc.display.shading.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = 900
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
mw = src.matrix_world
P = np.array([(mw @ v.co)[:] for v in me.vertices])
out = os.path.join(HERE, 'review', 'groups'); os.makedirs(out, exist_ok=True)
head = P[P[:, 2] > P[:, 2].max() - .32]
for name, pts, scale, views in (('body', P, 1.85, dict(front=(0, -1, .1), back=(0, 1, .1), side=(-1, 0, .1), q34=(.7, -.7, .3))),
                                ('head', head, .38, dict(front=(0, -1, .05), side=(-1, 0, .05), back=(0, 1, .2), top=(.1, -.3, 1)))):
    ctr = Vector(((pts.min(0) + pts.max(0)) / 2).tolist())
    for vn, dv in views.items():
        dv = Vector(dv).normalized(); cam.location = ctr + dv * 4; cam.data.ortho_scale = scale
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{name}_{vn}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED')
