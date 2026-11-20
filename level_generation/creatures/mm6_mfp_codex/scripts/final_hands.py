import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
code=(P/'scripts/final_sheets.py').read_text();exec(code[:code.index("for name in ['Standing'")])
for role,frame in [('Standing',0),('Attack',12.5)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=frame%1)
 for side in 'LR':
  h=r.pose.bones[f'B_{side}_Hand'].head;common.render_views(str(P/f'review/hand_{role}_{side}'),h.z-.025,.28,views=('front','left','three_quarter'),resolution=(600,600),target=(h.x,h.y))
# Measure nearest contact on the actual handle surface, separately for all five digits.
local=np.array([tuple(r.data.bones['Knife'].matrix_local.inverted()@v.co)for v in k.data.vertices]);faces=[tuple(f.vertices)for f in k.data.polygons if all(-.075<local[i,2]<.025 for i in f.vertices)];M=r.pose.bones['Knife'].matrix;tree=BVHTree.FromPolygons([tuple(M@Vector(v))for v in local],faces);gn={g.index:g.name for g in b.vertex_groups};ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();report={}
for digit,label in enumerate(['thumb','index','middle','ring','little']):
 ids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if gn[g.group].startswith(f'B_R_Finger{digit}'))>.5];dist=[tree.find_nearest(me.vertices[i].co)[3]*1000 for i in ids];report[label]={'vertices':len(ids),'minimum_actual_handle_surface_gap_mm':min(dist)}
ev.to_mesh_clear();(P/'review/grip_surface.json').write_text(json.dumps(report,indent=2));print('GRIP_SURFACE',report,flush=True)
