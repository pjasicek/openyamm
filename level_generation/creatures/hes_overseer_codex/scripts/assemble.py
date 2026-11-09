"""Assemble the sash and weapon sockets on the common winged rig. Save a provisional editable family."""
import bpy,bmesh,json,sys,os,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_actions.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=[v.co.copy() for v in body.data.vertices];groups={g.index:g.name for g in body.vertex_groups}
weight=[{groups[g.group]:g.weight for g in v.groups} for v in body.data.vertices]
def skin_tree(bones):
 faces=[tuple(f.vertices) for f in body.data.polygons if all(sum(w for n,w in weight[v].items() if n in bones)>.35 for v in f.vertices)]
 assert faces,bones
 return BVHTree.FromPolygons(co,faces,all_triangles=True),faces
TORSO=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_L_Clavicle','B_R_Clavicle']
fronttree,frontfaces=skin_tree(TORSO);legtree,legfaces=skin_tree(['B_Pelvis','B_R_Thigh','B_R_Calf','B_L_Thigh','B_L_Calf'])
cloth=bpy.data.materials.new('OV_Sash');cloth.use_nodes=True;cloth.use_backface_culling=True;b=cloth.node_tree.nodes.get('Principled BSDF');b.inputs['Roughness'].default_value=.94;b.inputs['Metallic'].default_value=0
tex=cloth.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures/overseer_sash_basecolor.png'));cloth.node_tree.links.new(tex.outputs['Color'],b.inputs['Base Color'])
# The material base stays neutral: only shared runtime ramps supply the rank colour.
def sample_weight(point,tree,faces):
 hit,n,fi,dist=tree.find_nearest(point);ids=faces[fi];A,B,C=[np.array(co[i]) for i in ids]
 uv=np.linalg.lstsq(np.column_stack([B-A,C-A]),np.array(hit)-A,rcond=None)[0];bar=np.clip(np.r_[1-uv.sum(),uv],0,1);bar/=bar.sum();w={}
 for vi,f in zip(ids,bar):
  for name,value in weight[vi].items():w[name]=w.get(name,0)+float(value*f)
 w=dict(sorted(w.items(),key=lambda kv:-kv[1])[:4]);total=sum(w.values());return {n:v/total for n,v in w.items()}
def ribbon(name,centres,widths,side='front',leg=False):
 tree,faces=(legtree,legfaces) if leg else (fronttree,frontfaces);nu=4;nv=len(centres);verts=[];weights=[];uvs=[];sg=-1 if side=='front' else 1
 for i,((x,z),width) in enumerate(zip(centres,widths)):
  for j in range(nu):
   xx=x+(j/(nu-1)-.5)*width;origin=Vector((xx,sg,z));direction=Vector((0,-sg,0));hit,n,fi,dist=tree.ray_cast(origin,direction)
   if hit is None:hit,n,fi,dist=tree.find_nearest(Vector((xx,0,z)))
   clearance=.045 if not leg else .022;point=Vector((xx,hit.y+sg*clearance,z));verts.append(point);weights.append(sample_weight(point,tree,faces));uvs.append((j/(nu-1)*.65,i/(nv-1)*4))
 # Fit a smooth cloth surface over the chest shell, without following individual skin ridges.
 if not leg:
  ys=np.array([v.y for v in verts]).reshape(nv,nu)
  smooth=ys.copy()
  for _ in range(3):
   a=np.pad(smooth,1,mode='edge');smooth=(4*a[1:-1,1:-1]+a[:-2,1:-1]+a[2:,1:-1]+a[1:-1,:-2]+a[1:-1,2:])/8
  for k,v in enumerate(verts):v.y=float(smooth.ravel()[k])
 G=len(verts);verts+= [v+Vector((0,-sg*.002,0)) for v in verts];weights+=weights.copy();uvs+=uvs.copy()
 faces=[]
 for i in range(nv-1):
  for j in range(nu-1):
   k=i*nu+j;faces.extend([(k,k+1,k+nu+1,k+nu),(G+k+nu,G+k+nu+1,G+k+1,G+k)])
 edge=[j for j in range(nu-1)]+[i*nu+nu-1 for i in range(nv-1)]+[(nv-1)*nu+j for j in range(nu-1,0,-1)]+[i*nu for i in range(nv-1,0,-1)]
 for a,c in zip(edge,edge[1:]+edge[:1]):faces.append((a,c,c+G,a+G))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(cloth)
 uv=me.uv_layers.new(name='UVMap')
 for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 vg={n:o.vertex_groups.new(name=n) for n in set(n for ws in weights for n in ws)}
 for i,ws in enumerate(weights):
  for n,w in ws.items():vg[n].add([i],w,'REPLACE')
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bmesh.ops.triangulate(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
 return o
for side in ['front','back']:
 ribbon('Sash_'+side,[(.10*(1-t)-.10*t,1.175*(1-t)+.865*t) for t in np.linspace(0,1,10)],[.058]*10,side)
for i,(dx,end) in enumerate([(-.023,.53),(.017,.59),(.043,.64)]):
 centres=[(-.08+dx+.01*math.sin(t*4),.845*(1-t)+end*t) for t in np.linspace(0,1,9)]
 ribbon('Sash_tail_'+str(i),centres,[.032*(1-.45*t) for t in np.linspace(0,1,9)],leg=True)
# All equipment is authored in its own canonical frame; a rigid socket carries that frame with the hand/hip.
with bpy.data.libraries.load(str(P/'work/equipment_meshy.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('OV_')]
gear={o.name:o for o in dst.objects}
for o in gear.values():bpy.context.scene.collection.objects.link(o)
grip=json.loads((P/'work/grip_pose.json').read_text());spec=[]
for part,node,sd in [('collar_rod','CollarRod','R'),('arc_maul','ArcMaul','R'),('pulse_pistol','PulsePistol','L')]:
 M=Matrix(grip[sd]['rotation_bind']).to_4x4();M.translation=Vector(grip[sd]['center_bind']);spec.append((part,node,f'B_{sd}_Hand',M))
for part,node,parent,position,rotation in [('plasma_saber','HipSaber','B_Pelvis',(-.23,.10,.74),math.radians(20)),('collar_key','CollarKey','B_Pelvis',(.168,-.25,.838),0)]:
 M=Matrix.Rotation(rotation,4,'Y');M.translation=position;spec.append((part,node,parent,M))
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for part,node,parent,M in spec:
 b=rig.data.edit_bones.new(node);b.head=M.translation;b.tail=b.head+M.to_3x3().col[1]*.05;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones[parent]
# A separate holster socket uses the same sidearm mesh, with its barrel hanging down.
M=Matrix.Rotation(math.pi,4,'Z')@Matrix.Rotation(math.pi/2,4,'X');M.translation=(-.18,.09,.78)
b=rig.data.edit_bones.new('HolsterPistol');b.head=M.translation;b.tail=b.head+M.to_3x3().col[1]*.05;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
for part,node,parent,M in spec:
 o=gear['OV_'+part];o.matrix_world=M
 # Bake the socket's bind frame into the mesh so split_attachment.py can later recover canonical node coordinates.
 for v in o.data.vertices:v.co=M@v.co
 o.matrix_world=Matrix.Identity(4);o.parent=rig;o.vertex_groups.clear();o.vertex_groups.new(name=node).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
 o['attachment_node']=node
for n,parent,point in [('Socket_Muzzle','PulsePistol',(0,-.373,.103)),('Socket_Rod','CollarRod',(0,0,.588)),('Socket_Maul','ArcMaul',(.14275,-.04607,.57))]:
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');M=rig.data.edit_bones[parent].matrix.copy();M.translation=M@Vector(point);b=rig.data.edit_bones.new(n);b.head=M.translation;b.tail=b.head+M.to_3x3().col[1]*.01;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones[parent];bpy.ops.object.mode_set(mode='OBJECT')
# Provisional A preview; other equipment remains available in the blend for the boss assemblies.
for name in ['OV_arc_maul','OV_plasma_saber','OV_collar_key']:gear[name].hide_render=True
# Projecting the back-facing belt can reverse its shell; orient each closed plate before export.
for o in [o for o in bpy.data.objects if o.name.startswith('Arm_')]:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free()
# Short belt hangers make the cleared hip equipment visibly attached to the existing belt.
hanger_mat=bpy.data.materials.new('OV_Hanger');hanger_mat.use_nodes=True;hanger_mat.use_backface_culling=True;bs=hanger_mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.027,.012,1);bs.inputs['Roughness'].default_value=.8
belt=np.array([v.co[:] for o in bpy.data.objects if o.name in ['Arm_belt_front','Arm_belt_back'] for v in o.data.vertices]);assert len(belt)
for node,part in [('HipSaber','plasma_saber'),('CollarKey','collar_key'),('HolsterPistol','pulse_pistol')]:
 points=np.array([v.co[:] for v in gear['OV_'+part].data.vertices])
 if node=='HolsterPistol':
  M=rig.data.bones[node].matrix_local@rig.data.bones['PulsePistol'].matrix_local.inverted();points=np.array([M@Vector(v) for v in points])
 distance=np.linalg.norm(belt[:,None,:]-points[None,:,:],axis=2);i,j=np.unravel_index(distance.argmin(),distance.shape);A=Vector(belt[i]);B=Vector(points[j]);axis=(B-A).normalized();A+=axis*.006;B-=axis*.002
 bpy.ops.mesh.primitive_cube_add(size=1,location=(A+B)/2);o=bpy.context.object;o.name='OV_'+node+'_hanger';o.rotation_euler=axis.to_track_quat('Z','Y').to_euler();o.scale=(.014,.004,(B-A).length);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(hanger_mat)
 o.parent=rig;o.vertex_groups.new(name=node).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig;o.hide_render=True
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/overseer_assembly.blend'))
print('ASSEMBLY_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
