import bpy,sys,os,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
for ver in ['v2t','v3','v4','v5','v6t','v7']:
 bpy.ops.wm.open_mainfile(filepath=str(p/f'work/rig_{ver}.blend'))
 ob=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];m=ob.data
 pv=np.zeros(len(m.vertices),np.int32);m.attributes['piece'].data.foreach_get('value',pv)
 ids=[v.index for v in m.vertices if pv[v.index]==1 and abs(v.co.x)>.27]
 names=[g.name for g in ob.vertex_groups]
 print('DIAG',ver,len(ids),[(tuple(round(x,3) for x in m.vertices[i].co),[(names[g.group],round(g.weight,3)) for g in m.vertices[i].groups if g.weight>.01]) for i in ids[::max(1,len(ids)//5)]],flush=True)
 if ver in ['v3','v4','v6t']:
  a=bpy.data.actions['Hit'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  bpy.context.scene.frame_set(3)
  common.workbench_clay(bpy.context.scene)
  common.render_views(str(p/f'review/diagnostic_{ver}'),.85,2.1,views=('front',),resolution=(600,700))
