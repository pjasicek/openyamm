from pathlib import Path
import bpy,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_grip.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
common.workbench_clay(scene);scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.65,.65,.65)
out=p/'review/motion_first';out.mkdir(exist_ok=True)
rows=[]
for action in ('Standing','Walking','Running','Attack','Hit','Death','Fidget'):
    act=bpy.data.actions[action];rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    for view in ('front','left'):
        row=[]
        for i,f in enumerate(np.linspace(*act.frame_range,5)):
            scene.frame_set(int(f),subframe=f-int(f))
            files=common.render_views(str(out/f'{action}_{i}'),.85,2.0,views=(view,),resolution=(400,440),target=(0,0))
            row.append([files[0],f'{action} {view} {f/30:.2f}s'])
        rows.append(row)
(out/'frames.json').write_text(json.dumps(rows))
