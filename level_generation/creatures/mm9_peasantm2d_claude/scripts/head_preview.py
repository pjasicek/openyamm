"""Quick textured preview of the head set (diagnosis, before a rebuild): head faces of a blend with textures/nj_head_final.png on HeadUV,
EEVEE-free workbench texture renders. Args: <blend> <out prefix> <view spec ...> (name:dx,dy,dz:cx,cy,cz:size)"""
import bpy, bmesh, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
for m in list(body.modifiers): body.modifiers.remove(m)
body.parent = None
import numpy as np
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if mat[f.index] != 2], context='FACES')
bm.to_mesh(me); bm.free()
me.uv_layers.active = me.uv_layers['HeadUV']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
m = bpy.data.materials.new('h'); m.use_nodes = True
tex = m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.abspath(os.path.join(os.path.dirname(a[0]), '..', 'textures', 'nj_head_final.png')))
bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); m.node_tree.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
me.materials.clear(); me.materials.append(m)
for p in me.polygons: p.use_smooth = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.3, 0.3, 0.32)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for sp in a[2:]:
    n, d, c, z = sp.split(':')
    d = Vector([float(x) for x in d.split(',')]).normalized(); c = Vector([float(x) for x in c.split(',')])
    cd.ortho_scale = float(z); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('PREVIEW done')
