"""Close frames of one clip: args <blend> <clip> <frames comma> <view loc x,y,z> <target x,y,z> <ortho> <out png>
[textured]. Clay (or textured) renders tiled into one sheet."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_render as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
blend, clip, frames, loc, tgt, orth, out = a[:7]; tex = len(a) > 7
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, blend))
rig = bpy.data.objects['Robot_Rig']; rig.animation_data.action = bpy.data.actions[clip]
cells = []
for f in [int(x) for x in frames.split(',')]:
    bpy.context.scene.frame_set(f); p = os.path.join(HERE, f'work/_fs_{f}.png')
    C.render_ortho(tuple(map(float, loc.split(','))), tuple(map(float, tgt.split(','))), float(orth), p, res=(420, 320),
                   textured=tex, mesh_name='Robot', rig_name='Robot_Rig'); cells.append(p)
C.sheet(os.path.join(HERE, out), cells, min(len(cells), 6))
for p in set(cells): os.remove(p)
print('SHEET', out)
