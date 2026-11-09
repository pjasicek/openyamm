"""Rest pose with bones: side, front, top, quarter, under -> review/rig_v1_<view>.png, plus a contact sheet."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
for v in ('side', 'front', 'top', 'quarter', 'under'):
    loc, tgt = C.VIEWS[v]
    C.render(loc, tgt, 1.2, os.path.join(HERE, 'review', f'rig_v1_{v}.png'), res=(700, 500), bones=True, floor=v != 'under')
