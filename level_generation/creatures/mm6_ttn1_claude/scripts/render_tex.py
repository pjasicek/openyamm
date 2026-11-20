"""Lit renders of the rest-pose titan with a base colour texture (Args: blend image tag [clip:frame]):
front, three-quarter, side, back and a head close-up, EEVEE with soft light."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Titan_Rig']; mesh = bpy.data.objects['Titan']
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
if len(a) > 3:
    clip, f = a[3].split(':'); act = bpy.data.actions[clip]; arm.animation_data.action = act
    if act.slots: arm.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(f))
m = bpy.data.materials.new('Tex'); m.use_nodes = True; nt = m.node_tree
b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Roughness'].default_value = 0.8
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(a[1]))
nt.links.new(t.outputs[0], b.inputs['Base Color'])
mesh.data.materials.clear(); mesh.data.materials.append(m)
sc = common.setup_render((600, 900))
sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.55, 0.58, 1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 2.5; sun.rotation_euler = (math.radians(50), 0, math.radians(-25))
for o in bpy.data.objects:
    o.hide_render = o.type == 'MESH' and o is not mesh
hips = arm.matrix_world @ arm.pose.bones['Hips'].head          # follow the hips in a clip frame
common.render_views(os.path.join(common.REVIEW, a[2]), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(600, 900), target=(float(hips.x), float(hips.y)))
common.render_views(os.path.join(common.REVIEW, a[2] + '_head'), 1.43, 0.34, views=('front', 'three_quarter'),
                    resolution=(500, 500))
