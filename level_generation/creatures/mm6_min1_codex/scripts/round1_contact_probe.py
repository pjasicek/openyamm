import bpy,runpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['gate','--','work/round1_clothed.blend'];g=runpy.run_path(str(P/'scripts/rig_gates_48.py'));r=g['rig'];b=g['body'];BVH=g['BVHTree'];out={}
for nm,f in [('Attack',105)]:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(int(f),subframe=f%1);pts=g['co'](b);out[str(f)]={}
 for s in 'RL':
  tree=BVH.FromPolygons(pts.tolist(),g['fl'][s])
  for part in ['hand','forearm']:
   faces=g['partfaces'][s][part];pairs=BVH.FromPolygons(pts.tolist(),faces).overlap(tree);ids=sorted({v for x,y in pairs for v in faces[x]});raw=g['depth'](tree,pts,g['parts'][s][part]);actual=g['depth'](tree,pts,ids);out[str(f)][s+part]={'overlaps':len(pairs),'raw':raw,'crossing_depth':actual,'hit_face':g['fl'][s][raw[2]] if raw[2] is not None else None,'sample':pts[raw[1]].tolist() if raw[1] is not None else None}
 common.workbench_clay(bpy.context.scene);common.render_views(str(P/f'review/round1/probe_{f}'),1.3,1.8,views=['front','left','three_quarter'],resolution=(700,700))
(P/'review/round1/contact_probe.json').write_text(json.dumps(out,indent=2));print('PROBE',out)
