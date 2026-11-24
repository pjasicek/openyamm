"""Close-up review renders for the D-118 repair (F57): posed frames of one clip from named cameras, textured or clay.
Usage: repair_views.py <blend under work/> <out dir> <clip> <frames comma list> <view[,view]> [scale] [textured 0|1]
Views: common.VIEWS plus 'mouth' (low front close-up), 'mouthq' (low three-quarter close-up), 'hop' (side, wide),
'belly' (top-down, for the dead pose). Writes <out>/<clip>_<view>_<frame>.png."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, clip, frames, views = a[0], a[1], a[2], [int(x) for x in a[3].split(',')], a[4].split(',')
scale = float(a[5]) if len(a) > 5 else 2.4
textured = len(a) > 6 and a[6] == '1'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
os.makedirs(out, exist_ok=True)
rig = bpy.data.objects['Toad_Rig']; sc = bpy.context.scene
act = bpy.data.actions[clip]
rig.animation_data.action = act
if len(getattr(act, 'slots', [])):
    rig.animation_data.action_slot = act.slots[0]
CAMS = dict(C.VIEWS)
CAMS.update({'mouth': ((0, -2.6, 0.55), (0, -0.6, 0.52)), 'mouthq': ((-1.4, -2.2, 0.75), (0, -0.6, 0.5)),
             'hop': ((4.5, -0.2, 0.6), (0, -0.2, 0.5)), 'belly': ((0.3, 0.2, 2.6), (0, 0, 0.2)),
             'side': ((4.5, -0.2, 0.45), (0, -0.2, 0.45))})
extra = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Mouth')]
TEX = {('Toad', 0): 'toad_basecolor_graded.png', ('Toad', 1): 'toad_mouth.png', ('Tongue', 0): 'toad_tongue.png'}
if textured:
    for (name, slot), png in TEX.items():
        o = bpy.data.objects.get(name)
        if o is None or (slot > 0 and len(o.data.materials) <= slot):
            continue
        mat = bpy.data.materials.new(f'view_{name}_{slot}'); mat.use_nodes = True
        n = mat.node_tree.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(os.path.join(HERE, 'textures', png))
        mat.node_tree.nodes.active = n
        if len(o.data.materials) > slot:
            o.data.materials[slot] = mat
        else:
            o.data.materials.append(mat)
for f in frames:
    sc.frame_set(f)
    for v in views:
        C.render(*CAMS[v], scale, os.path.join(out, f'{clip}_{v}_{f:02d}.png'), res=(520, 420), textured=textured,
                 extra=extra)
print('VIEWS', clip, frames, views)
