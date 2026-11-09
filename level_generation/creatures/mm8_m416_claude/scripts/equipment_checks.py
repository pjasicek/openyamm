"""Dense closed-surface prop contact, string endpoint and supported aiming checks."""
from pathlib import Path
import bpy,bmesh,json,sys,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/ready_final.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
piece=np.array([d.value for d in me.attributes['piece'].data]);faces=[tuple(f.vertices) for f in me.polygons];proxies=[];closure=[]
for part in [0,1,2,6,7]:
 fs=[f for f in faces if piece[f[0]]==part];ids=sorted({v for f in fs for v in f});bm=bmesh.new();at=bm.verts.layers.int.new('source');vs={}
 for i in ids:v=bm.verts.new(me.vertices[i].co);v[at]=i;vs[i]=v
 for f in fs:bm.faces.new([vs[i] for i in f])
 bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));closed=all(e.is_manifold for e in bm.edges);closure.append([part,closed]);assert closed,part;proxies.append((part,[tuple(v[at] for v in f.verts) for f in bm.faces]));bm.free()
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return co

def inside(tree,p):
 votes=0
 for d in [Vector((1,.271,.137)).normalized(),Vector((-.193,1,.317)).normalized(),Vector((.239,.173,1)).normalized()]:
  start=Vector(p);n=0
  for _ in range(48):
   hit,_,_,_=tree.ray_cast(start,d,10)
   if hit is None:break
   n+=1;start=hit+d*.00001
  votes+=n%2
 return votes>=2
cfg=json.loads((P/'work/props.json').read_text());relL=Matrix(json.loads((P/'work/prop_grips.json').read_text())['L']);report=json.loads((P/'review/equipment_checks.json').read_text())['roles'] if len(sys.argv)>1 and '--' in sys.argv else {}
for a in list(bpy.data.actions):
 if not a.use_fake_user or a.name=='Dead' or ('--' in sys.argv and sys.argv[sys.argv.index('--')+1:] and a.name not in sys.argv[sys.argv.index('--')+1:]):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst={};ground={};aim=[];strings=[];contact_frames={}
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));co=coords(o);trees=[(part,BVHTree.FromPolygons(co,fs)) for part,fs in proxies];CB=r.pose.bones['Crossbow'].matrix
  for i,s in enumerate('LR'):
   pb=r.pose.bones['String'+s];u=max(0,min(1,(f/30-1)*30));v=max(0,min(1,(f/30-1.4)/.1666667));amount=u*u*(3-2*u)*(1-v*v*(3-2*v)) if a.name=='Attack' else 0;nock=Vector(cfg['nock_drawn']).lerp(Vector(cfg['nock_released']),amount)
   strings.append(max((pb.matrix.translation-CB@Vector(cfg['string_tips'][i])).length,(pb.matrix@Vector((0,1,0))-CB@nock).length))
  if a.name=='Attack' and .65<=f/30<=1.2:aim.append((r.pose.bones['B_L_Hand'].matrix.translation-(CB@relL).translation).length)
  for name in ['CrossbowMesh','BoltMesh','QuiverMesh']:
   pc=coords(bpy.data.objects[name]);ground[name]=min(ground.get(name,1e9),float(pc[:,2].min()))
   for part,tree in trees:
    key=f'{name}_into_{part}'
    for point in pc:
     hit,norm,idx,dist=tree.find_nearest(Vector(point),.07)
     if hit is not None and dist>.002 and dist>worst.get(key,[0])[0] and (Vector(point)-hit).dot(norm)<-.7*dist and inside(tree,point):worst[key]=[float(dist),float(f)];contact_frames.setdefault(str(float(f)),{})[key]=float(dist)
 report[a.name]={'penetration_m':worst,'contact_frames':contact_frames,'minimum_ground_m':ground,'string_endpoint_max_m':max(strings),'aim_contact_max_m':max(aim,default=0)};print('EQUIPMENT',a.name,report[a.name],flush=True)
(P/'review/equipment_checks.json').write_text(json.dumps({'closure':closure,'roles':report},indent=2))
