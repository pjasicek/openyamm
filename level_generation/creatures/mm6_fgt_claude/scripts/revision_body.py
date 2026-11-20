"""User revision 1: seat pauldrons on pads and shorten cheek hair; preserve paid UVs and motion."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from common import setup_render,workbench_clay,render_views
bpy.ops.wm.open_mainfile(filepath=str(p/'review/revision1/rig_textured.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
pv=np.zeros(len(me.vertices),int);me.attributes['piece'].data.foreach_get('value',pv)
co=np.array([v.co[:] for v in me.vertices]);old_uv={l.name:np.array([v.uv[:] for v in l.data]) for l in me.uv_layers}
report={}
# Fit in the displayed standing pose, then invert the existing skin transform. This keeps the steel collar
# stable on the chest instead of stretching it between torso and rotating arm weights.
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());pm=ev.to_mesh();posed=[v.co.copy() for v in pm.vertices];ev.to_mesh_clear()
from mathutils import Matrix
transforms={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups}
for plate in [7,13]:
 sx=-1 if plate==7 else 1
 caps=[f.vertices[:] for f in me.polygons if all(pv[i] in (11,12) and co[i,0]*sx>0 for i in f.vertices)]
 tree=BVHTree.FromPolygons(posed,caps);moved=[]
 for i in np.where(pv==plate)[0]:
  v=me.vertices[i];x,y,z=co[i]
  if plate==7 and y>.11 and z<1.34:continue
  t=float(np.clip((abs(x)-.10)/.09,0,1));t=t*t*(3-2*t)
  tz=float(np.clip((z-1.31)/.08,0,1));t*=tz*tz*(3-2*tz)
  if t<=0:continue
  loc,n,fi,d=tree.find_nearest(posed[i]);dest=posed[i].lerp(loc+n*.010,t)
  matrix=Matrix([[sum(e.weight*transforms[e.group][r][c] for e in v.groups) for c in range(4)] for r in range(4)])
  old=v.co.copy();v.co=matrix.inverted()@dest;moved.append((v.co-old).length)
 report[str(plate)]={'vertices_seated':len(moved),'max_move_m':max(moved),'weights':'unchanged; inverse-skinned standing fit'}
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
# Recess the concealed pad surface slightly so coarse triangles cannot cut through the fitted steel rim.
for part in [11,12]:
 ids=np.where(pv==part)[0];centre=Vector(co[ids].mean(0))
 for i in ids:me.vertices[i].co=centre+(me.vertices[i].co-centre)*.94
 report[str(part)]={'scale_about_component_centre':.94}
for part in [26,27]:
 ids=np.where(pv==part)[0];top=co[ids,2].max();cx=co[ids,0].mean()
 for i in ids:
  v=me.vertices[i];v.co.z=top-(top-v.co.z)*.36
  t=(top-co[i,2])/(top-co[ids,2].min());v.co.x=cx+(v.co.x-cx)*(1-.3*t)
 report[str(part)]={'old_min_z':float(co[ids,2].min()),'new_min_z':min(me.vertices[i].co.z for i in ids)}
for l in me.uv_layers:assert np.array_equal(old_uv[l.name],np.array([v.uv[:] for v in l.data]))
# Keep the revision additive: the original paid textured rig remains the reproducible input.
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_revision1_body.blend'))
(p/'review/revision1/body_repair.json').write_text(json.dumps(report,indent=2))
me.materials.clear()
for i,c in enumerate([(.3,.3,.3,1),(.2,.5,.95,1),(.85,.3,.05,1),(.35,.1,.5,1)]):
 m=bpy.data.materials.new('part'+str(i));m.diffuse_color=c;me.materials.append(m)
for f in me.polygons:
 k=pv[f.vertices[0]];f.material_index=1 if k in (7,13) else 2 if k in (11,12) else 3 if k in (26,27) else 0
scene=setup_render();workbench_clay(scene)
for act in ['Standing','Walking','Attack','Death']:
 rig.animation_data.action=bpy.data.actions[act];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 scene.frame_set({'Standing':0,'Walking':12,'Attack':18,'Death':5}[act]);bpy.context.view_layer.update()
 render_views(str(p/'review/revision1'/('after_'+act)),1.37,.72,views=('front','three_quarter'),resolution=(850,850))
print('REPAIR',report)

import runpy
sys.argv=['g6_head_clearance.py','--',str(p/'work/rig_revision1_body.blend'),'Attack']
runpy.run_path(str(p/'scripts/g6_head_clearance.py'),run_name='__main__')
