"""Clip sheet: every clip at 6 times, side view (+X, the drone's left) with a floor plane at z 0, tier-A texture.
Args: -- <blend> <out_dir> [view: left|q]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_hdr as C
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = os.path.abspath(a[1]); view = a[2] if len(a) > 2 else 'left'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out, exist_ok=True)
rig = bpy.data.objects['HDR_Rig']; m = bpy.data.objects['HDR']
mat = bpy.data.materials.new('prev'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.join(HERE, 'work', 'tier_hdr_a.png'))
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
m.data.materials.clear(); m.data.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.001)); fl = bpy.context.active_object; fl.name = 'Floor'
fm = bpy.data.materials.new('floor'); fm.diffuse_color = (0.35, 0.4, 0.35, 1); fl.data.materials.append(fm)
if 'HDR_Thrust' in bpy.data.objects:
    bpy.data.objects['HDR_Thrust'].hide_render = True
clips = ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget']
d = {'left': (1, 0, 0.0), 'q': (0.7, -0.7, 0.35), 'front': (0, -1, 0.1)}[view]
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for i in range(6):
        f = round(f0 + (f1 - f0) * i / 5)
        bpy.context.scene.frame_set(int(f))
        c = (0, 0, 0.3); loc = [c[k] + 3 * d[k] for k in range(3)]
        C.render_ortho(loc, c, 1.1, os.path.join(out, f'{clip}_{i}.png'), show={'HDR', 'Floor'}, res=(300, 300), textured=True)
print('SHEET frames', out)
