import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduce_natf as red
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;objects=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']];sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'review/final/frames';out.mkdir(exist_ok=True)
common.workbench_clay(sc,True);sc.display.render_aa='32';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.display.shading.show_specular_highlight=False
for ob in objects:red.preview(ob,sel[ob.name]['0']['maps'],'natf_b');ob.hide_render=False
rows=json.loads((P/'review/final/frames.json').read_text())
for name in ['Attack']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];frames=np.array({'Attack':[.4326923077,.5729166667,.8701923077,1.0368589744,1.8333333333],'Hit':[0,.15,.27,.45,.7],'Death':[0,.1,.2,.34,1.3]}.get(name,np.linspace(0,a.frame_range[1]/sc.render.fps,5)))*sc.render.fps;bounds=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds(objects);bounds.append((lo,hi))
 lo=np.min([b[0]for b in bounds],0);hi=np.max([b[1]for b in bounds],0);center=(lo+hi)/2;span=hi-lo;height=max(1.84,span[2]*1.12,np.hypot(span[0],span[1])*1.7);rows[name]=[]
 for ix,f in enumerate(frames):
  sc.frame_set(int(f),subframe=float(f%1))
  for view in ['front','left','three_quarter']:
   file=common.render_views(str(out/f'{name}_{ix}'),center[2],height,views=(view,),resolution=(280,420),target=center[:2])[0];rows[name].append({'view':view,'frame':float(f),'path':str(Path(file).relative_to(P))})
(P/'review/final/frames.json').write_text(json.dumps(rows,indent=2))

# Refresh comparative close-ups on the final smoothed export.
import runpy
preview=runpy.run_path(str(P/'scripts/round5_preview.py'),run_name='__main__');warp=preview['warp']
# Reuse the shared anatomical measurements on original frames 48–64 and their retimed equivalents.
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
cfg=json.loads((P/'gates.json').read_text());result={}
for rev,path in [('before',P/'review/round5/before/export/mm6_natf.glb'),('after',P/'export/mm6_natf.glb')]:
 gb=g.Glb(path);ac=next(x for x in gb.doc['animations']if x['name']=='Attack');ts=np.arange(48,65)/48
 if rev=='after':ts=np.array([warp(t)for t in ts])
 rep=g.Report(cfg);g.bone_gates(gb,gb.pose(ac,ts),ts,'Attack',cfg,rep,[]);result[rev]={'sha256':gb.sha256,'rows':[r for r in rep.rows.values()if r['region']in ['R','R twist','B_R_UpperArm','B_R_Forearm','B_R_Hand']]}
(P/'review/round5/arm_window_shared_metrics.json').write_text(json.dumps(result,indent=2))
