import bpy,sys,os,math,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];HERE=str(p)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd)
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
me.uv_layers.active=me.uv_layers['HeadUV']
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for face in me.polygons:face.select=bool(hd[face.index])
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(30),island_margin=.004,scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=.004,shape_method='CONCAVE',merge_overlap=False)
bpy.ops.object.mode_set(mode='OBJECT')
def overlaps():
 me.calc_loop_triangles();uv=me.uv_layers['HeadUV'].data;owner=np.full((1024,1024),-1,np.int32);bad=set()
 for tri in me.loop_triangles:
  if not hd[tri.polygon_index]:continue
  ps=np.array([tuple(uv[l].uv) for l in tri.loops])*1024
  x0,y0=np.maximum(0,np.floor(ps.min(0)).astype(int));x1,y1=np.minimum(1023,np.ceil(ps.max(0)).astype(int))
  if x1<x0 or y1<y0:continue
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);a,b,c=ps
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-12:continue
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
  inside=(u>1e-7)&(v>1e-7)&((1-u-v)>1e-7);area=owner[y0:y1+1,x0:x1+1];hit=inside&(area>=0)
  if hit.any():bad.add(tri.polygon_index);bad.update(map(int,np.unique(area[hit])))
  area[inside]=tri.polygon_index
 return bad
for iteration in range(6):
 bad=overlaps();print('UV_ISOLATE',iteration,len(bad),flush=True)
 if not bad:break
 uv=me.uv_layers['HeadUV'].data
 for fi in bad:
  for li in me.polygons[fi].loop_indices:uv[li].uv.x+=.003+fi*1e-6
 bpy.ops.object.mode_set(mode='EDIT')
 bpy.ops.uv.pack_islands(margin=.004,shape_method='CONCAVE',merge_overlap=False,udim_source='ACTIVE_UDIM')
 bpy.ops.object.mode_set(mode='OBJECT')
assert not overlaps()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v9h2.blend'))
def export(which, out, uv):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
    if which == 'head':
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != uv]:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    for at in [x.name for x in ob.data.attributes if x.name in ('piece', 'finger', 'head', 'orig_co')]:
        ob.data.attributes.remove(ob.data.attributes[at])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
    print('UPLOAD', which, out, len(ob.data.polygons), 'faces')
    bpy.data.objects.remove(ob, do_unlink=True)



export('head',str(p/'texturing/nobl_head_upload_v2.glb'),'HeadUV')
b=bpy.data.objects['Body'];me=b.data;hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd);me.calc_loop_triangles()
report={}
for layer in ['HeadUV']:
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
