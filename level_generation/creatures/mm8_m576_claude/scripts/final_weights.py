import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work'
bpy.ops.wm.open_mainfile(filepath=str(W/'master_before_export_fit.blend'));ob=bpy.data.objects['Body'];count=0;removed=[]

for v in ob.data.vertices:
 entries=sorted([(e.group,e.weight) for e in v.groups if e.weight>0],key=lambda e:e[1],reverse=True);kept=entries[:4];total=sum(w for _,w in kept)
 assert total>0
 if len(entries)>4:count+=1;removed.append(sum(w for _,w in entries[4:]))
 for g,w in entries:ob.vertex_groups[g].remove([v.index])
 for g,w in kept:ob.vertex_groups[g].add([v.index],w/total,'REPLACE')
assert max(sum(e.weight>1e-8 for e in v.groups) for v in ob.data.vertices)<=4
# Put the fastest part of the downward thrust at native impact (1 s), retaining the reviewed poses.
a=bpy.data.actions['Attack']
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:
     old=float(k.co.x)
     if old<=21:new=old*25/21
     elif old<=30:new=25+(old-21)*10/9
     elif old<=33:new=35+(old-30)/3
     else:new=36+(old-33)*12/15
     shift=new-old;k.co.x=new;k.handle_left.x+=shift;k.handle_right.x+=shift
    fc.update()
(W/'attack_retime.json').write_text(json.dumps({'old_frames':[0,21,30,33,48],'new_frames':[0,25,35,36,48],'impact_seconds':1.0,'reason':'Fastest downward stroke crosses target at native impact; all reviewed poses retained.'},indent=2))

(W/'weight_cap.json').write_text(json.dumps({'affected_vertices':count,'maximum_removed_weight':max(removed,default=0)},indent=2));print('FOUR WEIGHTS',count,max(removed,default=0),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_weights4_uv.blend'))
sys.argv=['contact_fix.py','--',str(W/'master_weights4_uv.blend'),str(W/'master_textured_uv.blend')];runpy.run_path(str(P/'scripts/contact_fix.py'),run_name='__main__')
