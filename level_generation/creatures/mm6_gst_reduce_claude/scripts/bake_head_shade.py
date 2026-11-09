"""Native-style shade (short-range AO x top light, ../mm6_gst_codex/scripts/bake_native_shade.py) baked on the reduced
mesh in rest pose into its merged atlas layout; the head half is work/head_shade.npy (1024 x 1024, rows top-down).
Usage: blender -b -P bake_head_shade.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_head.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
body = bpy.data.objects['Cand_55']; body.hide_render = False; body.hide_set(False)
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
bpy.context.view_layer.update(); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
mat = bpy.data.materials.new('NativeShade'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
image = bpy.data.images.new('shade', 2080, 1024, alpha=False, float_buffer=True); image.colorspace_settings.name = 'Non-Color'
target = nt.nodes.new('ShaderNodeTexImage'); target.image = image; nt.nodes.active = target
ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .08
geo = nt.nodes.new('ShaderNodeNewGeometry'); dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
dot.inputs[1].default_value = (0, 0, 1); nt.links.new(geo.outputs['Normal'], dot.inputs[0])


def mad(socket, mul, add):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY_ADD'; nt.links.new(socket, n.inputs[0])
    n.inputs[1].default_value = mul; n.inputs[2].default_value = add; return n.outputs[0]


shade = nt.nodes.new('ShaderNodeMath'); shade.operation = 'MULTIPLY'
nt.links.new(mad(ao.outputs['AO'], .75, .25), shade.inputs[0]); nt.links.new(mad(dot.outputs['Value'], .45, .85), shade.inputs[1])
em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(shade.outputs[0], em.inputs['Color'])
out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs['Surface'])
body.data.materials.clear(); body.data.materials.append(mat)
for o in bpy.context.view_layer.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.bake(type='EMIT')
a = np.array(image.pixels[:], np.float32).reshape(1024, 2080, 4)[::-1, :, 0]
np.save(os.path.join(HERE, 'work', 'head_shade.npy'), a[:, 1056:])
print('SHADE head', float(a[:, 1056:].min()), float(a[:, 1056:].max()))
