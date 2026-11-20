import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data
base=np.empty(len(me.vertices)*3);me.attributes['orig_co'].data.foreach_get('vector',base);base=base.reshape(-1,3)
count=0;shift=0
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value!=0:continue
 co=base[v.index];sd='L' if co[0]>-.006 else 'R';a=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);z=np.array(r.data.bones[f'B_{sd}_Hand'].head_local);d=z-a;t=np.dot(co-a,d)/np.dot(d,d)
 weight=float(np.clip((abs(co[0]+.006)-.22)/.13,0,1))*float(np.clip((t+.2)/.8,0,1));weight=weight*weight*(3-2*weight)
 axis=a+d*t;new=axis+(co-axis)*(1-.32*weight);v.co=new;count+=weight>0;shift=max(shift,float(np.linalg.norm(new-co)))
(p/'work/sleeve_fit.json').write_text(json.dumps({'edited_vertices':int(count),'max_shift_m':shift,'reason':'Constrain oversized generated cuff flare to the native folded-sleeve pose; wrist/hand geometry and all joints unchanged.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/retarget_raw.blend'))
