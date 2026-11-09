"""Short-range AO (3 cm reach, as the Swordsman project's claude_shared/bake_creature_ao.py run) baked on the repaired,
re-UV'd pick in rest pose into its merged atlas layout; the body half is work/ao_body.npy (1024 x 1024, rows top-down); REA_SET=detail bakes the 2048 detail section of the final layout.
Usage: blender -b -P bake_body_ao.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SET = os.environ.get('REA_SET', 'body')          # detail: work/ladder_detail.blend, 3136-wide atlas, section at 2112
# body: 2080 x 1024 atlas, section at 0; detail: final 3104 x 2080 atlas (atlas_layout.py), 2048 section at x 1056
AW, AH, X0, S = (3104, 2080, 1056, 2048) if SET == 'detail' else (2080, 1024, 0, 1024)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_final.blend' if SET == 'detail' else f'ladder_{SET}.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
mesh = bpy.data.objects['Cand_62']; mesh.hide_render = False
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not mesh:
        o.hide_render = True
bpy.context.view_layer.update(); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
sc.world = sc.world or bpy.data.worlds.new('w'); sc.world.light_settings.distance = .03
img = bpy.data.images.new('ao', AW, AH, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for o in bpy.context.view_layer.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
a = np.array(img.pixels[:], np.float32).reshape(AH, AW, 4)[::-1, X0:X0 + S, 0][:S]
np.save(os.path.join(HERE, 'work', f'ao_{SET}.npy'), a)
print('AO', SET, float(a.min()), float(a.mean()))
