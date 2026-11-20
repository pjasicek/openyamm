from pathlib import Path
import bpy
p=Path(__file__).resolve().parents[1]
for name in ['ready_lined','ready_motion','ready_final']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/(name+'.blend')));me=bpy.data.objects['Body'].data;uv=me.uv_layers['UVMap'].data;g=me.attributes['garment'].data;count=0
 for f in me.polygons:
  if len(f.vertices)!=3 or not all(g[i].value in (1,5,6,12) for i in f.vertices):continue
  for li in f.loop_indices:
   x=uv[li].uv.x;uv[li].uv.x=(x-.75)*3 if x>=.75 else x/3+.75
  count+=1
 assert count==1386,count
 bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/(name+'.blend')));print('SWAPPED lining UV triangles',name,count)
