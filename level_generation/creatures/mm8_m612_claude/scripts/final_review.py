import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/portable_a.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
out=P/'review/animation_textured';out.mkdir(exist_ok=True)
common.workbench_clay(scene,textured=True);report={}
for name in ('Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'):
    if __import__('os').environ.get('GOG_REVIEW_CLIP',name)!=name:continue
    a=bpy.data.actions[name];rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    end=float(a.frame_range[1])
    for phase in (0,.25,.5,.75,1):
        f=end*phase;scene.frame_set(int(f),subframe=f%1)
        common.render_views(str(out/f'{name}_{phase:.2f}'),.85,2.9 if name in ('Death','Dead') else 2.45,
            views=('front','left','three_quarter'),resolution=(320,400))
    if name in ('Walking','Running'):
        pos=[]
        for f in np.arange(0,end+.1,.5):
            scene.frame_set(int(f),subframe=float(f%1))
            pos.append([list(rig.pose.bones[f'B_{s}_Foot'].head) for s in ('L','R')])
        pos=np.array(pos);speed=[];details=[]
        for i in range(2):
            z=pos[:,i,2];low=z<z.min()+.015
            vy=np.gradient(pos[:,i,1])*60
            speed.append(float(np.median(vy[low])))
            details.append({'samples':int(low.sum()),'median_backward_speed':speed[-1]})
        stride=float(np.mean(speed)*end/30)
        assert stride>0
        report[name]={'stride_length':stride,'duration':end/30,'feet':details,'stance_height_tolerance_m':.015}
if report:(P/'work/strides.json').write_text(json.dumps(report,indent=2)+'\n');print('STRIDES',report)
