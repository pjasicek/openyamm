"""Rebuild the reviewed equipment from the preserved v1 master and solved fist pose."""
from pathlib import Path
import bpy,bmesh,json,math,ast,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gripped_r2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
L=json.loads((P/'work/armour_layout.json').read_text());AT=L['atlas'];RECT={k:L['plates']['parts_'+k]['rect'] for k in ('resin','cloth','ivory','gold','hide')}
MATS=[bpy.data.materials['HKR_Plate'],bpy.data.materials['HKR_Glow']]
module=ast.parse((P/'scripts/build_parts.py').read_text())
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('uv','Part','tube','ring','horn')],type_ignores=[]),'build_parts_helpers','exec'))
height=max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices)
report={'body_height_m':height,'blades':{},'armour':{}}
def frame(g):
 z=Vector(g['handle_axis_hand_local']);x=Vector(g['blade_out_hand_local']);m=Matrix((x,z.cross(x),z)).transposed().to_4x4();m.translation=Vector(g['handle_centre_hand_local']);return m
for side in 'LR':
 old=json.loads((P/f'work/review_v1/grip_pose_{side}.json').read_text());new=json.loads((P/f'work/grip_pose_r2_{side}.json').read_text())
 H=rig.data.bones[f'B_{side}_Hand'].matrix_local;oldM=H@frame(old);newM=H@frame(new)
 for kind,ratio in (('Family',.58),('Vreth',.62)):
  ob=bpy.data.objects[f'{kind}_Blade_{side}'];coords=[oldM.inverted()@v.co for v in ob.data.vertices]
  adj={i:set() for i in range(len(coords))}
  for e in ob.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
  todo=set(adj);components=[]
  while todo:
   stack=[todo.pop()];comp=[]
   while stack:
    i=stack.pop();comp.append(i)
    for j in adj[i]&todo:todo.remove(j);stack.append(j)
   components.append(comp)
  span=max(v.z for v in coords)-min(v.z for v in coords);anchor=.15 if kind=='Vreth' else .12;scale=(height*ratio-2*anchor)/(span-2*anchor)
  for comp in components:
   central=max(abs(coords[i].z) for i in comp)<.17 and len(comp) in (16,30,12)
   if central:
    if len(comp)==16:
     for i in comp:coords[i].x*=.026/.017;coords[i].y*=.026/.017
    elif side=='R':
     for i in comp:coords[i].y=-coords[i].y
    continue
   for i in comp:
    p=coords[i];p.z=math.copysign(anchor+(abs(p.z)-anchor)*scale,p.z);p.x*=.76;p.y*=.85
   if all(any(f.material_index==1 and i in f.vertices for f in ob.data.polygons) for i in comp):
    assert len(comp)==40,len(comp)
    for j in range(0,len(comp),4):
     # The original tube's vertex order is ten four-vertex rings.
     ids=sorted(comp)[j:j+4];c=sum((coords[i] for i in ids),Vector())/4
     for i in ids:coords[i]=c+(coords[i]-c).normalized()*(.017 if j<36 else .003)
  for v,c in zip(ob.data.vertices,coords):v.co=newM@c
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  span=max(v.z for v in coords)-min(v.z for v in coords);report['blades'][ob.name]={'span_m':span,'body_fraction':span/height,'edge_width_m':.034,'handle_radius_m':.026}
# Fitted segmented shells use only the unchanged native limb surface as their radial support.
CO=[v.co.copy() for v in body.data.vertices];GI={g.index:g.name for g in body.vertex_groups}
DOM=[GI[max(v.groups,key=lambda g:g.weight).group] for v in body.data.vertices]
for side in 'LR':
 for partname,bn,end,segments,arc in (('forearm',f'B_{side}_Forearm',f'B_{side}_Hand',[(.30,.48),(.53,.72),(.77,.97)],155),('shin',f'B_{side}_Calf',f'B_{side}_Foot',[(.09,.39),(.47,.78)],140)):
  name=f'Arm_{partname}_{side}';old=bpy.data.objects[name];a=rig.data.bones[bn].head_local;b=rig.data.bones[end].head_local;axis=(b-a).normalized();centre=sum((v.co for v in old.data.vertices),Vector())/len(old.data.vertices);out=(centre-a-axis*(centre-a).dot(axis)).normalized();across=axis.cross(out)
  names={bn,end,bn+'Twist'};faces=[tuple(f.vertices) for f in body.data.polygons if any(DOM[i] in names for i in f.vertices)];tree=BVHTree.FromPolygons(CO,faces)
  oldprops=dict(old.items());bpy.data.objects.remove(old,do_unlink=True);part=Part(name,bn)
  rect=L['plates'][partname+'_'+side]['rect']
  for lo,hi in segments:
   V=[];UV=[];F=[]
   for layer in (0,1):
    for row,t in enumerate(np.linspace(lo,hi,3)):
     c=a.lerp(b,float(t))
     for col,ang in enumerate(np.linspace(-arc/2,arc/2,5)):
      d=out*math.cos(math.radians(ang))+across*math.sin(math.radians(ang));hit=tree.ray_cast(c,d,.25)[0]
      if hit is None:
       nearby=[(p-c).dot(d) for p,dom in zip(CO,DOM) if dom in names and abs((p-c).dot(axis))<.045 and (p-c).dot(d)>0]
       radius=max(nearby,default=.055)
      else:radius=(hit-c).length
      V.append(c+d*(radius+.019+layer*.008));x,y,w,h=rect;UV.append(((x+4+(w-8)*col/4)/AT,1-(y+4+(h-8)*row/2)/AT))
   for layer in range(2):
    for r in range(2):
     for c in range(4):i=layer*15+r*5+c;F.append((i,i+1,i+6,i+5))
   border=list(range(5))+[9,14,13,12,11,10,5]
   for i,j in zip(border,border[1:]+border[:1]):F.append((i,j,j+15,i+15))
   part.add(V,F,UV=UV)
  ob=part.finish()
  for k,v in oldprops.items():ob[k]=v
  ob['segment_count']=len(segments)
  report['armour'][name]={'segments':len(segments),'arc_degrees':arc,'triangles':len(ob.data.polygons)}
 # A proper wrist ring closes the gauntlet just above the fist.
 H=rig.data.bones[f'B_{side}_Hand'].matrix_local;part=Part('Cuff_'+side,f'B_{side}_Hand');V=[];F=[]
 for i in range(8):
  ang=i*math.tau/8;rad=Vector((math.cos(ang),0,math.sin(ang)))
  for j in range(3):
   q=j*math.tau/3;V.append(H@(Vector((.059*math.cos(ang),.012,.047*math.sin(ang)))+rad*.006*math.cos(q)+Vector((0,.006*math.sin(q),0))))
 for i in range(8):
  for j in range(3):F.append((i*3+j,i*3+(j+1)%3,((i+1)%8)*3+(j+1)%3,((i+1)%8)*3+j))
 part.add(V,F);part.finish()
# Thin folded, irregular cloth preserves each existing three-bone chain and animation.
for old in [o for o in bpy.data.objects if o.name.startswith(('Cloth_','Mantle_'))]:
 name=old.name;boss=name.startswith('Mantle_');idx=int(name[-1]);front=name.startswith('Cloth_F');base=[v.co.copy() for v in old.data.vertices[:15]];base2=[v.co.copy() for v in old.data.vertices[15:30]];base=[(a+b)/2 for a,b in zip(base,base2)];names=[name+'_'+str(k) for k in range(3)]
 part=Part(name,names[0],boss);V=[];W=[];UV=[];F=[];kind='hide' if boss and idx%2==0 else 'cloth'
 for row in range(7):
  t=row/6;pos=t*4;k=min(3,int(pos));f=pos-k;c=base[k*3+1].lerp(base[(k+1)*3+1],f);left=base[k*3].lerp(base[(k+1)*3],f);right=base[k*3+2].lerp(base[(k+1)*3+2],f);half=(right-left)*.44
  for col in range(3):
   edge=(col-1)*(1 if row<2 else [.84,1.0,.56,.86,.23][row-2]);p=c+half*edge
   p.x+=.005*math.sin(row*2.2+idx);p.y+=.012*math.sin(row*1.8+col*2.4+idx)
   if row==6:p.z+=[.018,.0,.044][(col+idx)%3]
   seg=min(2,int(t*3));u=t*3-seg;weights={names[seg]:1.} if seg==2 else {names[seg]:1-u,names[seg+1]:u}
   V.append(p);W.append(weights);UV.append(uv(kind,col/2,t))
 for row in range(6):
  for col in range(2):i=row*3+col;F.append((i,i+1,i+4,i+3))
 part.add(V,F,kind,UV=UV,weights=W)
 # Small branching cracks, not a continuous bright outline.
 for branch,cols in enumerate(((1,1,0,1,1),(1,2,1))):
  start=1+branch*2;cv=[];cw=[];cf=[]
  for j,col in enumerate(cols):
   i=(start+j)*3+col;p=V[i]+Vector((0,-.0015 if front else .0015,0));p.x+=.004*math.sin(j*3+idx)
   cv.extend([p+Vector((-.0008,0,0)),p+Vector((.0008,0,0))]);cw.extend([W[i],W[i]])
  for j in range(len(cols)-1):cf.append((2*j,2*j+1,2*j+3,2*j+2))
  part.add(cv,cf,'gold',1,weights=cw)
 bpy.data.objects.remove(old,do_unlink=True);part.finish()
for image in bpy.data.images:
 if image.source=='FILE':
  try:image.reload()
  except RuntimeError:pass
report['components']={o.name:sum(len(f.vertices)-2 for f in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'}
for kind in ('family','vreth'):
 total=sum(n for name,n in report['components'].items() if not (kind=='family' and name.startswith('Vreth_') and name!='Vreth_Scars') and not(kind=='vreth' and name.startswith('Family_')))
 report[kind+'_total']=total;assert total<=15000,(kind,total)
assert len(body.data.polygons)==9408
(P/'review/r2/components.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/revised_r2.blend'));print(json.dumps(report),flush=True)
