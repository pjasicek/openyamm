"""Render the rig as sticks inside the semi-transparent mesh (EEVEE). Args: blend tag."""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
tag = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Peasant_Rig']
bm = bmesh.new()
for b in rig.pose.bones:
    h = rig.matrix_world @ b.head; t = rig.matrix_world @ b.tail
    d = t - h; L = d.length
    if L < 1e-5: continue
    r = 0.004 if 'Hand' in b.name and b.name[-1] in '123' else 0.007
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r * 0.4, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=Matrix.Translation((h + t) / 2) @ q.to_matrix().to_4x4(), verts=geom['verts'])
me = bpy.data.meshes.new('Sticks'); bm.to_mesh(me); sticks = bpy.data.objects.new('Sticks', me)
bpy.context.scene.collection.objects.link(sticks)
red = bpy.data.materials.new('red'); red.use_nodes = True
next(n for n in red.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.9, 0.05, 0.05, 1)
next(n for n in red.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Emission Color'].default_value = (0.9, 0.05, 0.05, 1)
next(n for n in red.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Emission Strength'].default_value = 1.0
me.materials.append(red)
glass = bpy.data.materials.new('glass'); glass.use_nodes = True
bs = next(n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); bs.inputs['Alpha'].default_value = 0.25
glass.surface_render_method = 'BLENDED' if hasattr(glass, 'surface_render_method') else None
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name not in ('Sticks',):
        o.hide_render = o.name in ('Proxy', 'SimLegs', 'SimSkirt') or o.name.startswith('Meshy')
        if not o.hide_render:
            o.data.materials.clear(); o.data.materials.append(glass)
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine; break
    except TypeError:
        pass
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.7, 0.7, 0.7, 1)
scene.view_settings.view_transform = 'Standard'
common.render_views(os.path.join(common.REVIEW, f'{tag}_skel'), 0.8, 1.7, views=('front', 'left'), resolution=(700, 700))
for side, x in (('Right', -0.38), ('Left', 0.38)):
    h = rig.matrix_world @ rig.pose.bones[f'mixamorig:{side}Hand'].head
    common.render_views(os.path.join(common.REVIEW, f'{tag}_skel_hand{side}'), h.z - 0.07, 0.22, views=('front', 'right' if side == 'Right' else 'left'),
                        resolution=(500, 500), target=(h.x, h.y))
common.render_views(os.path.join(common.REVIEW, f'{tag}_skel_head'), 1.38, 0.42, views=('front', 'left'), resolution=(500, 500))
common.render_views(os.path.join(common.REVIEW, f'{tag}_skel_feet'), 0.18, 0.45, views=('front', 'left'), resolution=(500, 500))
