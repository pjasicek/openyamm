import bpy,sys,runpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];rows=[]
for margin in [.01,.02,.03,.04]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));body=bpy.data.objects['Jackalman'];body.name='Body'
 for v,a in zip(body.data.vertices,body.data.attributes['piece'].data):
  if a.value!=1:continue
  x,y,z=v.co;t=max(0,min(1,(1.08-z)/.12));t=t*t*(3-2*t);r=max(math.hypot(x,y),.01);v.co.x+=margin*t*x/r;v.co.y+=margin*t*y/r
 file=P/f'work/skirt_margin_{margin:.2f}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));sys.argv=['gate','--',str(file),'Death'];runpy.run_path(str(P/'scripts/g6_skirt_poke.py'),run_name='__main__');row=json.loads((P/'work/g6_fauld.json').read_text())['Death'];row.update(margin_m=margin,blend=str(file.relative_to(P)));rows.append(row);print('MARGIN',row,flush=True)
 if row['depth_m']<=.002:break
(P/'review/round2/skirt_margin_trials.json').write_text(json.dumps(rows,indent=2))
