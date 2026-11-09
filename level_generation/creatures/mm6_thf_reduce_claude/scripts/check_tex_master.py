"""Review of work/master_tex.blend: faces coloured by texture set with a UV checker (body grey, cloak green, head the
installed head image), front and back; and the UV triangles of each set -> review/tex/master_*.png, uv_*.json."""
import bpy, json, math, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_tex.blend'))
mesh = bpy.data.objects['Thief']; rig = bpy.data.objects['Thief_Rig']
os.makedirs(os.path.join(HERE, 'review', 'tex'), exist_ok=True)
S = 512
def checker(tint):
    img = bpy.data.images.new('chk', S, S); y, x = np.mgrid[0:S, 0:S] / S
    g = ((np.floor(x * 16) + np.floor(y * 16)) % 2) * 0.4 + 0.4
    img.pixels = np.concatenate([np.stack([g * tint[0], g * tint[1], g * tint[2]], -1), np.ones((S, S, 1))], -1).ravel(); return img
def mat(m, img):
    m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
mats = mesh.data.materials
mat(mats[0], checker((0.9, 0.9, 0.9))); mat(mats[1], checker((0.4, 1.0, 0.4)))
head_img = bpy.data.images.load(os.path.join(HERE, 'textures', 'thf_head_basecolor_1k.png'))
mat(mats[2], head_img)
sc = bpy.context.scene
act = bpy.data.actions['Standing']; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.3, .3, .33, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600; sc.render.engine = 'BLENDER_EEVEE'
for view, dv, size, cz in [('front', Vector((0, -1, .1)), 1.9, .8), ('back', Vector((0, 1, .1)), 1.9, .8), ('face', Vector((0, -1, .05)), .45, 1.45)]:
    c = Vector((0, 0, cz)); dv.normalize(); cam.location = c + dv * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    sc.render.filepath = os.path.join(HERE, 'review', 'tex', f'master_{view}.png'); bpy.ops.render.render(write_still=True)
import bmesh
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
ts = [d.value for d in mesh.data.attributes['tex_set'].data]
json.dump({str(k): [[[l[uv].uv.x, l[uv].uv.y] for l in f.loops] for f in bm.faces if ts[f.index] == k] for k in (0, 1, 2)},
          open(os.path.join(HERE, 'review', 'tex', 'uv_sets.json'), 'w'))
