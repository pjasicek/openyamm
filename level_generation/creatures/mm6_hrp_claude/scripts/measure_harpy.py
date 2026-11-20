"""Measure anatomical regions and section centres before fitting the six-limb rig."""
from pathlib import Path
import bpy,bmesh,json
import numpy as np
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));o=bpy.data.objects['Body'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);parts=np.array([v.value for v in me.attributes['part'].data])
left=np.where(parts==1)[0];tree=kdtree.KDTree(len(left))
for i in left:tree.insert(Vector((-co[i,0]-.02,co[i,1],co[i,2])),int(i))
tree.balance();wing=(parts==1)
for i in np.where((co[:,0]<-.05)&(co[:,2]>1.08))[0]:
 if tree.find(Vector(co[i]))[2]<.045:wing[i]=True
# A wing's leading contour gives the skeleton and its broad trailing sheet follows span stations.
np.save(P/'work/wing_mask.npy',wing)
for side,sg in [('L',1),('R',-1)]:
 print('WING',side)
 for x in [.1,.25,.4,.6,.8,1.,1.2,1.4]:
  a=co[wing&(abs(co[:,0]-sg*x)<.045)]
  if len(a):print(x, np.round(np.quantile(a,[0,.5,1],axis=0),3).tolist())
 print('ARM',side)
 for z in np.arange(.84,1.401,.06):
  a=co[(~wing)&(parts==0)&(abs(co[:,2]-z)<.018)&(co[:,0]*sg>.22)]
  if len(a):print(round(z,2),np.round(np.median(a,0),3).tolist(),len(a))
 print('LEG',side)
 for z in np.arange(.18,1.01,.07):
  a=co[(parts==0)&(abs(co[:,2]-z)<.018)&(co[:,0]*sg>.04)&(co[:,0]*sg<.3)]
  if len(a):print(round(z,2),np.round(np.median(a,0),3).tolist(),len(a))
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();boundary=[e for e in bm.edges if e.is_boundary];seen=set();loops=[]
for e in boundary:
 if e in seen:continue
 todo=[e];ids=set()
 while todo:
  q=todo.pop()
  if q in seen:continue
  seen.add(q);ids.update(v.index for v in q.verts)
  for v in q.verts:todo.extend(x for x in v.link_edges if x.is_boundary and x not in seen)
 c=co[list(ids)];loops.append({'verts':len(ids),'center':c.mean(0).tolist(),'size':np.ptp(c,axis=0).tolist()})
(P/'work/boundaries.json').write_text(json.dumps(loops,indent=2));print('BOUNDARIES',loops)
bm.free()
attr=me.color_attributes.new('Anatomy','FLOAT_COLOR','POINT');me.color_attributes.active_color=attr
for i,v in enumerate(attr.data):v.color=(.7,.09,.06,1) if wing[i] else (.45,.5,.55,1)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='VERTEX';sc.display.shading.show_cavity=True;sc.render.resolution_x=1000;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('World');sc.world.color=(.12,.12,.12)
cam=bpy.data.objects.new('MeasureCamera',bpy.data.cameras.new('MeasureCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,size in [('wing_front',(0,-6,1.2),(0,0,1.2),3.2),('wing_back',(0,6,1.2),(0,0,1.2),3.2),('wing_side',(6,0,1.2),(0,0,1.2),1.6),('hand',(2,-4,1.1),(.55,-.08,.77),.38),('foot',(2,-4,.4),(.25,-.01,.15),.55)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'measure_{name}.png');bpy.ops.render.render(write_still=True)
