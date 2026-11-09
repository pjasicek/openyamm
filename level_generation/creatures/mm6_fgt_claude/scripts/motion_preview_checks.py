"""Existing deformation gates plus dense armour contact checks for the two changed motions."""
from pathlib import Path
import bpy, sys, runpy, json, numpy as np
P=Path(__file__).resolve().parents[1]
OPTIONS=globals().get('ATTACK_OPTIONS',False)
OUT=globals().get('REVIEW_OUT',P/('review/attack_options' if OPTIONS else 'review/motion_preview'))
ACTS=list(json.loads((OUT/'motion_sources.json').read_text()))
sys.path.insert(0,str(P/'scripts'))
blend=globals().get('REVIEW_BLEND',P/('work/rig_attack_options.blend' if OPTIONS else 'work/rig_motion_preview.blend'))
old=(P/'work/g6_contacts.json').read_bytes()
try:
 for name in ('g6_contacts.py','g6_head_clearance.py','g4_skirt.py','g6_skirt_poke.py','g5_hand_stretch.py'):
  sys.argv=[str(P/'scripts'/name),'--',str(blend),*ACTS]
  runpy.run_path(sys.argv[0],run_name='__main__')
 (OUT/'body_contacts.json').write_bytes((P/'work/g6_contacts.json').read_bytes())
finally:(P/'work/g6_contacts.json').write_bytes(old)
sys.argv=[str(P/'scripts/g4_weights.py'),'--',str(blend),OUT.name,*[f'{name}:{frame}' for name in ACTS for frame in (0,12,18,24,30,36)]]
runpy.run_path(sys.argv[0],run_name='__main__')
from shoulder_intersections import intersections
bpy.ops.wm.open_mainfile(filepath=str(blend));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
me=body.data;me.calc_loop_triangles();parts=np.zeros(len(me.vertices),int);me.attributes['piece'].data.foreach_get('value',parts)
ids=np.where(parts==11)[0];si=np.where(parts==7)[0]
def faces(ids):
 lookup={int(v):i for i,v in enumerate(ids)}
 return np.array([[lookup[v] for v in t.vertices] for t in me.loop_triangles if all(v in lookup for v in t.vertices)])
pf=faces(ids);sf=faces(si);rows={}
for name in ACTS:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 row={'samples':0,'crossings':[]}
 for f in np.arange(0,act.frame_range[1]+.0001,30/192):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  hits=intersections(co[si],sf,co[ids],pf);row['samples']+=1
  if hits:row['crossings'].append([float(f)/30,len(hits)])
 rows[name]=row;print('SHOULDER',name,'samples',row['samples'],'crossing samples',len(row['crossings']),flush=True)
(OUT/'shoulder_gate.json').write_text(json.dumps(rows,indent=2)+'\n')
