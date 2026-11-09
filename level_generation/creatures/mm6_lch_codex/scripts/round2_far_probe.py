import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';W=P/'work/round2';sys.dont_write_bytecode=True
with bpy.data.libraries.load(str(P/'review/triangle_reduction/baseline/work/rig_textured.blend'),link=False)as(a,b):b.objects=['Body']
original=b.objects[0];me=original.data;pv=[x.value for x in me.attributes['piece'].data];source={};me.calc_loop_triangles()
for piece in set(pv):
 ids=[v.index for v in me.vertices if pv[v.index]==piece];verts=[me.vertices[i].co.copy()for i in ids];remap={v:i for i,v in enumerate(ids)};fs=[tuple(remap[i]for i in t.vertices)for t in me.loop_triangles if pv[t.vertices[0]]==piece]
 source[piece]={'tree':BVHTree.FromPolygons(verts,fs,all_triangles=True),'lo':np.min(verts,0),'hi':np.max(verts,0)}
camcfg=json.loads((R/'camera.json').read_text());reports=[]
for level in [1,2,3]:
 for mode in ['bounds','surface','surface_bounds']:
  bpy.ops.wm.open_mainfile(filepath=str(W/f'lod{level}_selected.blend'));sc=bpy.context.scene;ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];cam=sc.camera
  for o in bpy.data.objects:o.hide_render=o not in [ob,rig,cam]
  attrs=ob.data.attributes['piece'];pieces=np.array([x.value for x in attrs.data]);coords=np.array([tuple(v.co)for v in ob.data.vertices])
  for piece in set(pieces):
   ids=np.where(pieces==piece)[0];src=source[piece];points=coords[ids];lo=points.min(0);hi=points.max(0)
   if 'surface'in mode:
    for i in ids:
     hit=src['tree'].find_nearest(ob.data.vertices[i].co)
     if hit[0]is not None:ob.data.vertices[i].co=hit[0]
    points=np.array([tuple(ob.data.vertices[i].co)for i in ids]);lo=points.min(0);hi=points.max(0)
   if 'bounds'in mode:
    scale=(src['hi']-src['lo'])/np.maximum(hi-lo,1e-6)
    for i,point in zip(ids,points):ob.data.vertices[i].co=Vector(src['lo']+(point-lo)*np.clip(scale,.5,2))
  ob.data.update();rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
  dest=R/'silhouette'/f'far{level}_{mode}'/f'lod{level}';dest.mkdir(parents=True,exist_ok=True);res=camcfg['canvas_px'][level]
  sc.render.resolution_x=sc.render.resolution_y=res;cam.data.ortho_scale=camcfg['height_m']*res/camcfg['actor_height_px'][level];center=Vector(camcfg['center_m']);views=[]
  for k in range(8):
   ang=k*math.pi/4;cam.location=center+Vector((math.sin(ang),-math.cos(ang),0))*6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest/f'{k}.png');bpy.ops.render.render(write_still=True)
   masks=[]
   for file in [R/f'silhouette/baseline/lod{level}/{k}.png',dest/f'{k}.png']:
    im=bpy.data.images.load(str(file),check_existing=False);px=np.array(im.pixels[:]).reshape(res,res,4);masks.append(px[:,:,3]>.5);bpy.data.images.remove(im)
   a,b=masks;views.append({'intersection':int((a&b).sum()),'union':int((a|b).sum()),'iou':float((a&b).sum()/(a|b).sum())})
  report={'level':level,'mode':mode,'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons),'pooled_iou':sum(v['intersection']for v in views)/sum(v['union']for v in views),'min_iou':min(v['iou']for v in views),'views':views}
  bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}_{mode}.blend'));reports.append(report);print('FAR_PROBE',report,flush=True)
(R/'far_probe.json').write_text(json.dumps(reports,indent=2)+'\n')
