from pathlib import Path
import bpy,bmesh,json
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
j=json.loads((p/'work/meshy_joints.json').read_text())['joints']
bounds=json.loads((p/'work/geometry_boundaries_v2.json').read_text())
for side,part in [('L','P03'),('R','P04')]:
 loops=next(x['boundary_loops'] for x in bounds if x['part']==part)
 j[side+'_Hand']=max(loops,key=lambda x:x['edges'])['centre']
# Fit only the concealed legs, never slice the surrounding robe as if it were skin.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if me.attributes['piece'].data[v.index].value!=12],context='VERTS')
for side,sign in [('L',1),('R',-1)]:
 for joint in ['Calf','Foot']:
  old=j[side+'_'+joint];sl=bm.copy()
  cut=bmesh.ops.bisect_plane(sl,geom=list(sl.verts)+list(sl.edges)+list(sl.faces),plane_co=Vector(old),plane_no=(0,0,1))
  pts=np.array([tuple(v.co) for v in cut['geom_cut'] if isinstance(v,bmesh.types.BMVert) and v.co.x*sign>0])
  assert len(pts)>5
  centre=pts.mean(0);j[side+'_'+joint]=centre.tolist();sl.free()
bm.free()
report={'height_m':1.7,'joints':j,'method':'Meshy axial/shoulder/elbow estimates; wrist boundary rings; isolated trouser-leg sections at knees/ankles'}
(p/'work/joints_final.json').write_text(json.dumps(report,indent=2)+'\n')
