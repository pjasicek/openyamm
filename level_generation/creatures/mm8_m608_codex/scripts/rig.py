"""Fit stone-body joints and consolidate the generated boulder rollers before texturing."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/components.blend'))
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def join(objects,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o
def coords(o):return np.array([v.co[:] for v in o.data.vertices])
objects=[o for o in bpy.data.objects if o.type=='MESH']
upper=[o for o in objects if max(v.co.z for v in o.data.vertices)>.42]
lower=[o for o in objects if o not in upper]
eyes=[o for o in upper if min(v.co.z for v in o.data.vertices)>.89]
band=[o for o in upper if max(v.co.z for v in o.data.vertices)<.50 and abs(coords(o)[:,0].mean())<.15]
body=join([o for o in upper if o not in eyes and o not in band],'Torso')
band=join(band,'Band')
eye=join(eyes,'Eyes')
# Group generated rock fragments by their lateral roller, then remove overlapping interior shells.
centres=np.array([coords(o).mean(0) for o in lower]);seeds=np.array([[-.25,-.075,.21],[0,.015,.21],[.255,.10,.21]])
labels=np.argmin(((centres[:,None,:2]-seeds[None,:,:2])**2).sum(2),axis=1)
rollers=[];roller_info=[]
for i,x in enumerate([-.26,0,.26]):
 o=join([obj for j,obj in enumerate(lower) if labels[j]==i],f'Roller_{i}')
 c=coords(o);lo=c.min(0);hi=c.max(0);centre=(lo+hi)/2
 # Preserve crags, fit a round rolling envelope, and leave air between the three boulders.
 for v in o.data.vertices:
  p=(np.array(v.co)-centre)/(hi-lo)
  v.co=(x+p[0]*.22,.04+p[1]*.37,.20+p[2]*.38)
 bm=bmesh.new()
 for v in o.data.vertices:bm.verts.new(v.co)
 bm.verts.ensure_lookup_table();bmesh.ops.convex_hull(bm,input=bm.verts[:],use_existing_faces=False)
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free()
 c=coords(o);c[:,2]-=c[:,2].min()
 for v,p in zip(o.data.vertices,c):v.co=p
 centre=np.array([x,.04,(c[:,2].min()+c[:,2].max())/2])
 rollers.append(o);roller_info.append(dict(name=o.name,centre=centre.tolist(),bounds=[c.min(0).tolist(),c.max(0).tolist()],triangles=len(o.data.polygons)))
# Split at the natural stone neck; the head gets independent texture density.
active(body)
for v in body.data.vertices:v.select=v.co.z>.825
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
head=next(o for o in bpy.context.selected_objects if o!=body);head.name='Head'
active(body);dec=body.modifiers.new('BodyBudget','DECIMATE');dec.ratio=.70;bpy.ops.object.modifier_apply(modifier=dec.name)
for o in [body,head,band,*rollers]:
 for f in o.data.polygons:f.use_smooth=True
 # Edge sharpness follows geometric breaks; normals will split again on UV seams at export.
 bm=bmesh.new();bm.from_mesh(o.data)
 for e in bm.edges:e.smooth=not(e.is_manifold and e.calc_face_angle()>math.radians(45))
 bm.to_mesh(o.data);bm.free()
chains={
 'Root':(None,[(0,.04,0),(0,.04,.1)],['Root']),
 'Spine':('Root',[(0,.05,.45),(0,.065,.59),(0,.075,.77)],['Waist','Chest']),
 'Neck':('Chest',[(-.012,.06,.81),(-.012,.045,.865),(0,-.075,.90)],['Neck','Head'])}
for side,s in [('L',1),('R',-1)]:
 chains[side]=('Chest',[(s*.215,.075,.755),(s*.303,.063,.612),(s*.327,-.047,.507),(s*.285,-.123,.447)],[f'UpperArm_{side}',f'Forearm_{side}',f'Hand_{side}'])
for r in roller_info:
 c=np.array(r['centre']);chains[r['name']]=('Root',[c.tolist(),(c+[.1,0,0]).tolist()],[r['name']])
arm=bpy.data.armatures.new('JuggernautRig');rig=bpy.data.objects.new('JuggernautRig',arm);bpy.context.collection.objects.link(rig);active(rig)
bpy.ops.object.mode_set(mode='EDIT')
for key,(parent,points,names) in chains.items():
 previous=arm.edit_bones.get(parent) if parent else None
 for i,name in enumerate(names):
  b=arm.edit_bones.new(name);b.head=points[i];b.tail=points[i+1];b.parent=previous;b.use_connect=i>0
  b.align_roll(Vector((0,-1,0)));previous=b
bpy.ops.object.mode_set(mode='OBJECT')
def rigid(o,name):
 o.vertex_groups.clear();g=o.vertex_groups.new(name=name);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
def skin(o):
 o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
rigid(band,'Waist');rigid(head,'Head');rigid(eye,'Head')
for o in rollers:rigid(o,o.name)
names=['Waist','Chest','Neck']+[f'{part}_{side}' for side in ['L','R'] for part in ['UpperArm','Forearm','Hand']]
for n in names:body.vertex_groups.new(name=n)
c=coords(body);weights=np.zeros((len(c),len(names)))
for i,p in enumerate(c):
 x,y,z=p;side='L' if x>0 else 'R'
 if abs(x)>.18 and z<.74:allowed=[f'{part}_{side}' for part in ['UpperArm','Forearm','Hand']]
 else:allowed=['Waist','Chest','Neck',f'UpperArm_{side}']
 if z<.49 and abs(x)>.18:allowed=[f'Hand_{side}']
 for n in allowed:
  b=arm.bones[n];h=np.array(b.head_local);d=np.array(b.tail_local)-h;u=np.clip((p-h)@d/(d@d),0,1);distance=np.linalg.norm(p-h-u*d)
  weights[i,names.index(n)]=1/(distance+.009)**5
 weights[i]/=weights[i].sum()
edges=np.array([e.vertices[:] for e in body.data.edges]);degree=np.bincount(edges.ravel(),minlength=len(c))
for _ in range(3):
 average=np.zeros_like(weights);np.add.at(average,edges[:,0],weights[edges[:,1]]);np.add.at(average,edges[:,1],weights[edges[:,0]])
 weights=.7*weights+.3*average/np.maximum(degree[:,None],1);weights/=weights.sum(1)[:,None]
for i,w in enumerate(weights):
 keep=np.argsort(w)[-4:];total=w[keep].sum()
 for j in keep:
  if w[j]>1e-6:body.vertex_groups[names[j]].add([i],float(w[j]/total),'REPLACE')
for o in [body,head,band,eye,*rollers]:skin(o)
# Keep semantic assignments in face attributes for UV-space masks and rigid rubble ownership.
for o in [body,band,*rollers]:
 a=o.data.attributes.new('band','BOOLEAN','FACE')
 for d in a.data:d.value=o==band
body=join([body,band,*rollers],'Body')
for o in [body,head]:
 active(o)
 for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
 o.data.uv_layers.new(name='UVMap');bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(62),island_margin=.008,area_weight=0,scale_to_bounds=False)
 bpy.ops.uv.pack_islands(margin=.008,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
 assert all(v.groups for v in o.data.vertices)
for name,bone,pos in [('Socket_Palm_Left','Hand_L',(.29,-.13,.455)),('Socket_Palm_Right','Hand_R',(-.29,-.13,.455)),('Socket_Eye_Left','Head',(.007,-.077,.904)),('Socket_Eye_Right','Head',(-.032,-.078,.905))]:
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=rig;o.parent_type='BONE';o.parent_bone=bone
 bpy.context.view_layer.update();o.matrix_world.translation=Vector(pos)
rig.show_in_front=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
for o,name in [(body,'body'),(head,'head')]:
 duplicate=o.copy();duplicate.data=o.data.copy();duplicate.parent=None;duplicate.modifiers.clear();bpy.context.collection.objects.link(duplicate);active(duplicate)
 bpy.ops.export_scene.gltf(filepath=str(P/f'texturing/{name}_neutral.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
 bpy.data.objects.remove(duplicate,do_unlink=True)
(P/'work/rig_info.json').write_text(json.dumps(dict(chains=chains,rollers=roller_info,triangles={o.name:len(o.data.polygons) for o in [body,head,eye]},bones=len(arm.bones)),indent=2))
print('RIG_UV_OK',len(arm.bones),len(body.data.polygons),len(head.data.polygons),flush=True)
