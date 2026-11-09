"""Frame all anatomy explicitly; the source template camera clipped a long-tailed body."""
from pathlib import Path
import sys
import bpy
import numpy as np
p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/st_v1_parts.blend'))
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.65, 0.65, 0.65)
common.render_views(str(p / 'review/body_v1'), 0.85, 1.95,
                    views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(1000, 1000), target=(0, -0.25))
common.render_views(str(p / 'review/head_v1'), 1.5, 0.55,
                    views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(600, 600), target=(0, -0.5))
for side, x in (('left', 0.52), ('right', -0.52)):
    common.render_views(str(p / 'review' / ('hand_v1_' + side)), 0.83, 0.4,
                        views=('front', 'three_quarter'), resolution=(600,600), target=(x, -0.5))
co=np.array([tuple(v.co) for v in bpy.data.objects['P00'].data.vertices])
for y in np.arange(-0.35, 0.85, 0.1):
    v=co[(abs(co[:,1]-y)<0.025)&(co[:,2]<1.12)]
    if len(v):print('TAILSLICE',round(float(y),3),len(v),'mean',v.mean(0).round(3),'lo',v.min(0).round(3),'hi',v.max(0).round(3))
