import bpy,sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
d=json.loads((P/'work/deformation_v1.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
b=bpy.data.objects['Body']
for clip in ('Attack','Death'):
 for i in d[clip]['arm']['worst']['edge']:
  v=b.data.vertices[i]
  print('WORST',clip,i,tuple(round(x,4) for x in v.co),[(b.vertex_groups[g.group].name,round(g.weight,4)) for g in v.groups])
os.environ['INSPECT_BLEND']='animated_grounded.blend';os.environ['INSPECT_REPORT']='deformation_pre_twist.json'
runpy.run_path(str(P/'scripts/inspect_animation.py'),run_name='__main__')
