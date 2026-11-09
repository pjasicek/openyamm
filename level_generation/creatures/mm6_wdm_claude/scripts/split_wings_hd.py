"""Wing vertices of the HD base (work/hd_base.blend, rig frame): connected region grown from the wing tips through
candidates — behind the back (y above the spine's back surface at that height + 2 cm, off the spine) between the waist
and the shoulders, or above the head (the wrist hooks and upper struts). Writes work/wing_mask.npy and
review/wing_split_hd_<view>.png."""
import bpy, os
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Demon']; me = mesh.data
co = np.array([tuple(v.co) for v in me.vertices])
zs = np.arange(0.85, 1.45, 0.025)
back = []
for z in zs:
    s = co[(np.abs(co[:, 2] - z) < 0.0125) & (np.abs(co[:, 0]) < 0.05)]
    back.append(s[:, 1].max() if len(s) else 0.0)
back = np.array(back)
back_y = np.interp(co[:, 2], zs, back)
cand = ((co[:, 1] > back_y + 0.02) & (np.abs(co[:, 0]) > 0.04) & (co[:, 2] > 0.9)) | \
       ((co[:, 2] > 1.40) & (np.abs(co[:, 0]) > 0.09))
adj = [[] for _ in range(len(co))]
for e in me.edges:
    a, b = e.vertices
    adj[a].append(b); adj[b].append(a)
wing = np.zeros(len(co), bool)
stack = list(np.nonzero(cand & (np.abs(co[:, 0]) > 0.4) & (co[:, 2] > 1.3))[0])
wing[stack] = True
while stack:
    a = stack.pop()
    for b in adj[a]:
        if cand[b] and not wing[b]:
            wing[b] = True; stack.append(b)
np.save(os.path.join(HERE, 'work', 'wing_mask.npy'), wing)
print('WING verts', int(wing.sum()), 'of', len(co), 'L', int((wing & (co[:, 0] > 0)).sum()), 'R', int((wing & (co[:, 0] < 0)).sum()))
col = me.color_attributes.new('split', 'FLOAT_COLOR', 'POINT')
for i, w in enumerate(wing):
    col.data[i].color = (0.9, 0.2, 0.2, 1) if w else (0.75, 0.75, 0.75, 1)
me.color_attributes.active_color = col
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 700, 800
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
for name, d in (('front', (0, 1, 0)), ('back', (0, -1, 0)), ('side', (-1, 0, 0)), ('top', (0, 0.2, -1))):
    d = Vector(d).normalized(); cam.location = Vector((0, 0, 0.95)) - d * 5
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'wing_split_hd_{name}.png'); bpy.ops.render.render(write_still=True)
me.color_attributes.remove(col)
