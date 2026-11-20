"""Rest-pose renders of a work blend's Body with a given base colour (rework 2026-10-30 checks).
Args: -- <blend> <out dir> <prefix> <basecolor png> [views=front,back,top,q34] [size=900] [ortho=3.4] [head png]
With a head png and a 'head' face attribute + HeadUV layer, head faces show that texture on HeadUV."""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, outd, pre, tex = a[:4]
views = (a[4] if len(a) > 4 else 'front,back,top,q34').split(',')
size = int(a[5]) if len(a) > 5 else 900
ortho = float(a[6]) if len(a) > 6 else 3.4
headtex = a[7] if len(a) > 7 else None
os.makedirs(outd, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = body.parent
if rig and rig.animation_data:
    rig.animation_data.action = None
if rig:
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()


def mat(name, img, uv):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img)
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv
    nt.links.new(u.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    return m


me = body.data
me.materials.clear()
me.materials.append(mat('B', os.path.abspath(tex), 'UVMap'))
if headtex and 'head' in me.attributes and 'HeadUV' in me.uv_layers:
    me.materials.append(mat('H', os.path.abspath(headtex), 'HeadUV'))
    hd = [0] * len(me.polygons); me.attributes['head'].data.foreach_get('value', hd)
    me.polygons.foreach_set('material_index', hd)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.context.view_layer.update()
P = [body.matrix_world @ v.co for v in me.vertices]
c = Vector([(min(p[i] for p in P) + max(p[i] for p in P)) / 2 for i in range(3)])
if len(a) > 8:
    c = Vector([float(x) for x in a[8].split(',')])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.32, 0.33, 0.36)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': (-1.0, -1.25, 0.55), 'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0),
        'top': (0, 0.0001, 1), 'q34l': (1.0, -1.25, 0.55)}
for v in views:
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outd, f'{pre}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED', pre, views)
