from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_full_uv.blend'));o=bpy.data.objects['Body'];piece=o.data.attributes['piece'].data
for v in o.data.vertices:
 if piece[v.index].value!=1 or v.co.z>=1.51:continue
 z=v.co.z;levels=[('B_Pelvis',1.18),('B_Spine',1.29),('B_Spine1',1.40),('B_Spine2',1.51)];a,b=next(((a,b) for a,b in zip(levels,levels[1:]) if z<=b[1]),levels[-2:]);w=max(0,min(1,(z-a[1])/(b[1]-a[1])))
 for g in o.vertex_groups:g.remove([v.index])
 o.vertex_groups[a[0]].add([v.index],1-w,'REPLACE');o.vertex_groups[b[0]].add([v.index],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_ready.blend'))
for n,args in [('assemble_equipment',[P/'work/textured_ready.blend']),('fix_death',[]),('ground_final',[]),('final_equipment_motion',[]),('measure_runtime',[]),('export_runtime',[])]:
 s=P/'scripts'/(n+'.py');sys.argv=[str(s),'--',*map(str,args)] if args else [str(s)];runpy.run_path(str(s),run_name='__main__')
