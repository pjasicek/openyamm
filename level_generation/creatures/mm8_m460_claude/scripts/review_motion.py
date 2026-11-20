import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
args=sys.argv[sys.argv.index('--')+1:]
source=args[0] if args else 'motion_robed'
folder=args[1] if len(args)>1 else 'robed'
bpy.ops.wm.open_mainfile(filepath=str(p/f'work/{source}.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
out=p/f'review/{folder}';out.mkdir(parents=True,exist_ok=True)
common.workbench_clay(scene)
for role in ['Standing','Walking','Attack','Hit','Death']:
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];last=int(a.frame_range[1])
    for f in sorted(set([0,round(last*.25),round(last*.5),round(last*.75),last])):
        scene.frame_set(f)
        common.render_views(str(out/f'{role}_{f:03d}'),.9,2.8,views=('front','left','three_quarter'),resolution=(400,520))
