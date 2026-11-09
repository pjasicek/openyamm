"""Review renders of work/master.blend: body with its installed texture, head faces with a UV grid, the maw island with
a ring/spoke test pattern. Fly, Hit peak, Attack peak, Death mid; side and front. -> review/master/*.png"""
import bpy, math, os, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master.blend'))
rig = bpy.data.objects['Bld_Rig']; mesh = bpy.data.objects['Bld']
info = json.load(open(os.path.join(HERE, 'work', 'master.json')))
# test texture for the head: UV grid plus the maw island as rings and spokes
S = 1024; img = bpy.data.images.new('headtest', S, S)
y, x = np.mgrid[0:S, 0:S] / S
grid = ((np.floor(x * 16) + np.floor(y * 16)) % 2) * 0.35 + 0.45
rgb = np.stack([grid * 0.6, grid * 0.8, grid * 0.6], -1)
mc, mr = info['maw_uv_centre'], info['maw_uv_radius']
d = np.hypot(x - mc[0], y - mc[1]) / mr; ang = np.arctan2(y - mc[1], x - mc[0])
inside = d <= 1.0
rgb[inside] = np.stack([0.9 * np.ones(inside.sum()), 0.3 + 0.5 * ((np.floor(d[inside] * 5) % 2)), 0.2 + 0.6 * (np.floor(ang[inside] / (np.pi / 8)) % 2)], -1)
img.pixels = np.concatenate([rgb, np.ones((S, S, 1))], -1).ravel()
body_img = bpy.data.images.load('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_bld_claude/textures/bld_a_basecolor_graded.png')
def mat(name, image):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = image
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); m.use_backface_culling = False; return m
mesh.data.materials.clear(); mesh.data.materials.append(mat('body', body_img)); mesh.data.materials.append(mat('head', img))
head = mesh.data.attributes['head'].data
for p in mesh.data.polygons:
    p.material_index = head[p.index].value
sc = bpy.context.scene
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.3, .3, .33, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 420; sc.render.engine = 'BLENDER_EEVEE'
def use(name):
    act = bpy.data.actions[name]; ad = rig.animation_data; ad.action = act
    if act.slots: ad.action_slot = act.slots[0]
def peak(name):
    fc = next(fc for l in bpy.data.actions[name].layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves
              if fc.data_path == 'pose.bones["Maw"].scale' and fc.array_index == 0)
    return int(max(fc.keyframe_points, key=lambda k: k.co[1]).co[0])
os.makedirs(os.path.join(HERE, 'review', 'master'), exist_ok=True)
for clip in ['Fly', 'Hit', 'Attack', 'Death']:
    use(clip); f = 0 if clip == 'Fly' else peak(clip); sc.frame_set(f)
    c = rig.matrix_world @ rig.pose.bones['Mouth'].head
    for view, dv, size in [('side', Vector((1, 0, .1)), .7), ('front', Vector((0, -1, .2)), .7), ('q34', Vector((.7, -.7, .3)), .7)]:
        dv.normalize(); cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review', 'master', f'{clip}_{view}.png'); bpy.ops.render.render(write_still=True)
print('CHECK done')
# UV layout of the head set (polygons for review/master/head_uv.png, drawn outside Blender)
import bmesh
bm = bmesh.new(); bm.from_mesh(mesh.data); uv = bm.loops.layers.uv.active; hl = bm.faces.layers.int['head']
json.dump([[[l[uv].uv.x, l[uv].uv.y] for l in f.loops] for f in bm.faces if f[hl]],
          open(os.path.join(HERE, 'review', 'master', 'head_uv.json'), 'w'))
