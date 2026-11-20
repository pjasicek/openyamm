"""Replace subpixel feather shells with rigid sector envelopes before far-LOD reduction."""
import bpy,bmesh,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B
from reduction_render import render

def hull(name,points,material,bone,part):
 bm=bmesh.new();verts=[bm.verts.new(v)for v in points];bmesh.ops.convex_hull(bm,input=verts,use_existing_faces=False)
 used=set(v for f in bm.faces for v in f.verts);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in used],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(material);o.vertex_groups.new(name=bone).add(list(range(len(me.vertices))),1,'REPLACE');me.attributes.new('piece','INT','POINT').data.foreach_set('value',[part]*len(me.vertices));return o

def collapse(o,target):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Envelope collapse','DECIMATE');m.ratio=min(1,target/max(C.triangles(o),1));m.use_collapse_triangulate=True;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)

def join(base,others):
 bpy.ops.object.select_all(action='DESELECT')
 for o in [base]+others:o.select_set(True)
 bpy.context.view_layer.objects.active=base;bpy.ops.object.join()

def unwrap(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.context.tool_settings.mesh_select_mode=(False,False,True)
 for i in range(len(o.data.materials)):
  for f in o.data.polygons:f.select=f.material_index==i
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.006,area_weight=.25,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')

rows=[]
for level,pixels,cap,hbudget in [(2,220,3050,750),(3,88,1220,430)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));C.reset();r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);feathers=~np.isin(pv,[0,1,2,3,10,12,15]);groups={};gn={g.index:g.name for g in body.vertex_groups}
 for part in np.unique(pv[feathers]):
  ids=np.flatnonzero(pv==part);cent=np.mean([me.vertices[i].co[:]for i in ids],axis=0);weights={}
  for i in ids:
   for g in me.vertices[i].groups:
    name=gn[g.group]
    if name in r.data.bones:weights[name]=weights.get(name,0)+g.weight
  bone=max(weights,key=weights.get);origin=r.data.bones[bone].head_local;angle=math.atan2(cent[1]-origin.y,cent[0]-origin.x);sector=int((angle+math.pi)/(math.pi/2))%4;groups.setdefault((bone,sector),[]).extend(tuple(me.vertices[i].co)for i in ids)
 proxies=[]
 for i,((bone,sector),points)in enumerate(groups.items()):
  if len(points)<4:continue
  o=hull(f'Feather envelope {i}',points,me.materials[0],bone,1000+i);proxies.append(o)
 total=sum(C.triangles(o)for o in proxies)
 for o in proxies:collapse(o,max(8,round(C.triangles(o)*hbudget/total)))
 hulltris=sum(C.triangles(o)for o in proxies);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i]for i in np.flatnonzero(feathers)],context='VERTS');bm.to_mesh(me);bm.free()
 # Reserve the actual cloth topology and a few sole/grip contacts; face detail is in the rebaked normal map.
 for g in list(body.vertex_groups):
  if g.name.startswith('_'):body.vertex_groups.remove(g)
 pg=body.vertex_groups.new(name='_reduction_protect');pv=np.array([x.value for x in me.attributes['piece'].data]);pg.add(list(range(len(me.vertices))),.05,'REPLACE');ids=np.flatnonzero(np.isin(pv,[1,10]));pg.add(ids.tolist(),1,'REPLACE')
 for side in [-1,1]:
  ids=[v.index for v in me.vertices if pv[v.index]==0 and v.co.z<.009 and v.co.x*side>0]
  for axis in [0,1]:
   if ids:pg.add([min(ids,key=lambda i:me.vertices[i].co[axis]),max(ids,key=lambda i:me.vertices[i].co[axis])],1,'REPLACE')
 C.reduce(body,(cap-hulltris-8)/C.triangles(body),True);join(body,proxies)
 # A far spear uses connected shaft sections. Fine wraps stay in the near LODs and rebaked maps.
 spear=bpy.data.objects['SpearMesh'];inv=r.data.bones['Spear'].matrix_local.inverted();co=np.array([tuple(inv@v.co)for v in spear.data.vertices]);edges=np.linspace(co[:,2].min()-.00001,co[:,2].max()+.00001,8 if level==2 else 6);pieces=[]
 for i,(lo,hi)in enumerate(zip(edges,edges[1:])):
  ids=np.flatnonzero((co[:,2]>=lo-.008)&(co[:,2]<=hi+.008))
  if len(ids)>=4:
   o=hull(f'Shaft {i}',[spear.data.vertices[j].co[:]for j in ids],spear.data.materials[0],'Spear',2000+i);collapse(o,52 if level==2 else 28);pieces.append(o)
 oldname=spear.name;bpy.data.objects.remove(spear,do_unlink=True);spear=pieces.pop(0);spear.name=oldname;join(spear,pieces);spear.parent=r;m=spear.modifiers.new('Rig','ARMATURE');m.object=r
 buckler=bpy.data.objects['BucklerMesh'];collapse(buckler,400 if level==2 else 160)
 report={'level':level,'height_pixels':pixels,'triangles':{o.name:C.triangles(o)for o in [body,spear,buckler]},'feather_sectors':len(groups),'feather_triangles':hulltris}
 tex=P/f'work/reduction/lod{level}_envelopes'
 for o,kind in [(body,'body'),(spear,'spear'),(buckler,'buckler')]:
  # Envelope geometry spans former pieces; bake against the assembled high surface, not exploded pieces.
  if 'piece'in o.data.attributes:o.data.attributes['piece'].name='semantic_piece'
  unwrap(o);B.bake(o,tex/kind)
  if 'semantic_piece'in o.data.attributes:o.data.attributes['semantic_piece'].name='piece'
 dest=P/f'work/lod{level}_envelopes.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True);out=P/f'review/reduction/lod{level}_envelopes';render(dest,out,tex,pixels)
 visual=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/f'review/reduction/lod{level}_reference'),str(out)],text=True));v=list(visual['views'].values());u=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in v];pooled=sum(x['iou']*y for x,y in zip(v,u))/sum(u);visual['pooled_iou']=pooled;report.update(visual=visual,blend=str(dest.relative_to(P)),textures=str(tex.relative_to(P)));rows.append(report);(P/'review/reduction/lod_envelopes_curve.json').write_text(json.dumps(rows,indent=2));print('ENVELOPES',level,report['triangles'],pooled,visual['min_ssim'],flush=True)
