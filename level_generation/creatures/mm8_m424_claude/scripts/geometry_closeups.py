"""Head and both hands before any model repair."""
from pathlib import Path
import bpy
import sys
import json
sys.path.insert(0,str(Path(__file__).parent))
import common
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/st_v1_head_full'),1.565,0.32,
                    views=('front','left','back','three_quarter'),resolution=(600,600))
for side,x in [('left',0.48),('right',-0.48)]:
    common.render_views(str(p/('review/st_v1_hand_'+side)),0.95,0.29,
                        views=('front','back'),resolution=(600,600),target=(x,0))
body=bpy.data.objects['P00']
ears=[{'index':v.index,'co':list(v.co)} for v in body.data.vertices
      if abs(v.co.x)>0.066 and 1.54<v.co.z<1.65]
(p/'work/ear_vertices.json').write_text(json.dumps(ears,indent=2))
print('HEAD_HANDS',len(ears),'ear candidate vertices')
