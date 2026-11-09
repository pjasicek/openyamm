"""Close the shaft-to-hook neck after raised ferrules were baked away; fixed topology."""
import bpy,sys,runpy
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
for level in range(4):
 me=bpy.data.objects['Staff' if level==0 else f'Staff_LOD{level}'].data
 links={i:set()for i in range(len(me.vertices))}
 for e in me.edges:a,b=e.vertices;links[a].add(b);links[b].add(a)
 todo=[min(me.vertices,key=lambda v:v.co.z).index];shaft=set(todo)
 while todo:
  for v in links[todo.pop()]-shaft:shaft.add(v);todo.append(v)
 count=0
 for i in shaft:
  v=me.vertices[i]
  if v.co.z>.345:
   radius=v.co.xy.length
   if radius>0:v.co.x*=.016/radius;v.co.y*=.016/radius
   if v.co.z>.355:v.co.z=.366
   count+=1
 me.update();print('neck',level,count,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
runpy.run_path(str(P/'scripts/round4_rebake_final.py'),run_name='__main__')
