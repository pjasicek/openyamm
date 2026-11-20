import bpy,runpy,json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];report=[]
for level in [1,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1_lod{level}.blend'));body=bpy.data.objects['Body'];changed=0;largest=0
 for uv in body.data.uv_layers['UVMap'].data:
  for axis in range(2):
   x=uv.uv[axis]
   if x<0 or x>1:
    error=max(-x,x-1);assert error<.002;largest=max(largest,error);uv.uv[axis]=min(1,max(0,x));changed+=1
 assert changed<=6
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1_lod{level}.blend'));report.append({'level':level,'changed_uv_components':changed,'max_collapse_extrapolation':largest})
(P/'review/round1/uv_cleanup.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(P/'scripts/round1_geometry_lods.py'))
