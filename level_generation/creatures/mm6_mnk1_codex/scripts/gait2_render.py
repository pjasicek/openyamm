"""Textured workbench frames of the gait2 clips (and the old Walking) from front, side and three-quarter, composed into
review/gait2/<clip>_<view>.png sheets. Args: -- [blend] [clips...]"""
import bpy,sys,os
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
blend=a[0] if a else 'work/gait2.blend';clips=a[1:] or ['Walking','Walk2','Run2']
bpy.ops.wm.open_mainfile(filepath=str(p/blend))
sc=bpy.context.scene;r=bpy.data.objects['Rig'];common.workbench_clay(sc,textured=True)
out=p/'review/gait2/frames';out.mkdir(parents=True,exist_ok=True)
for clip in clips:
 act=bpy.data.actions[clip];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];end=int(act.frame_range[1])
 for f in np.linspace(0,end,7)[:-1]:
  f=float(round(f*2)/2);sc.frame_set(int(f),subframe=f%1)
  common.render_views(str(out/f'{clip}_{f:04.1f}'),.9,2.0,views=('front','left','three_quarter'),resolution=(360,480))
print('RENDERED')
