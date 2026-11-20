import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15.blend'))
b=bpy.data.objects['Body'];me=b.data;hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd);me.calc_loop_triangles()
report={}
for layer in ['UVMap','HeadUV']:
 uv=me.uv_layers[layer].data;counts=np.zeros((1024,1024),np.int16);areaUV=area3D=0.
 for tri in me.loop_triangles:
  if bool(hd[tri.polygon_index])!=(layer=='HeadUV'):continue
  ps=np.array([tuple(uv[l].uv) for l in tri.loops]);assert np.isfinite(ps).all() and ps.min()>-1e-5 and ps.max()<1.00001
  areaUV+=abs(float(np.cross(ps[1]-ps[0],ps[2]-ps[0])))*.5;area3D+=tri.area
  ps*=1024;x0,y0=np.maximum(0,np.floor(ps.min(0)).astype(int));x1,y1=np.minimum(1023,np.ceil(ps.max(0)).astype(int))
  if x1<x0 or y1<y0:continue
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);a,bb,c=ps
  den=(bb[1]-c[1])*(a[0]-c[0])+(c[0]-bb[0])*(a[1]-c[1])
  if abs(den)<1e-12:continue
  w0=((bb[1]-c[1])*(xx-c[0])+(c[0]-bb[0])*(yy-c[1]))/den
  w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
  inside=(w0>1e-7)&(w1>1e-7)&((1-w0-w1)>1e-7)
  counts[y0:y1+1,x0:x1+1]+=inside
 overlap=int((counts>1).sum());report[layer]={'overlap_pixels':overlap,'covered_pixels':int((counts>0).sum()),'texels_per_meter':1024*math.sqrt(areaUV/area3D),'surface_m2':area3D}
 assert overlap==0,(layer,overlap)
(p/'work/uv_audit.json').write_text(json.dumps(report,indent=1));print('UV_AUDIT',report)
for tier in 'abc':
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/f'review/viewer/mm6_nobl_{tier}.glb'))
 sc=bpy.context.scene;r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 common.workbench_clay(sc,True)
 common.render_views(str(p/f'review/tier_{tier}'),.85,2.15,views=('front','back','three_quarter'),resolution=(700,840))
 if tier!='a':continue
 # Lit PBR close-ups complement the unlit texture and full-body checks.
 sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=700;sc.view_settings.view_transform='Standard'
 sc.world=bpy.data.worlds.new('Neutral');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.2,.2,.2,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 for name,loc,power,size in [('Key',(-2,-3,3),250,3),('Fill',(2,-1,2),150,3),('Rim',(0,3,3),180,2)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 common.render_views(str(p/'review/lit_head'),1.52,.52,views=('front','left','three_quarter'),resolution=(700,700))
 common.render_views(str(p/'review/lit_body'),.85,2.0,views=('front','three_quarter'),resolution=(700,900))
