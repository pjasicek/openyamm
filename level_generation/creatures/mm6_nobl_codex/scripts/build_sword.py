"""Native straight sword from the sprite: broad gold guard, blue grip, round pommel."""
import bpy,bmesh,math,json,os,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7s.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# The rear tunic panel is hidden beneath the full-length cloak; omit its redundant inner surface.
bm=bmesh.new();bm.from_mesh(body.data);part=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]==8],context='VERTS')
bm.to_mesh(body.data);bm.free()
G=json.loads((p/'work/grip_pose.json').read_text());H=rig.data.bones['B_R_Hand'].matrix_local
c=H@Vector(G['handle_centre_hand_local']);ax=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
kn=rig.data.bones['B_R_Finger2'].head_local;side=kn-c;side=(side-ax*side.dot(ax)).normalized()
roll=math.radians(float(os.environ.get('BLADE_ROLL','45')));side=side*math.cos(roll)+ax.cross(side)*math.sin(roll);flat=ax.cross(side)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones.new('Sword');eb.head=c;eb.tail=c+ax*.15;eb.parent=rig.data.edit_bones['B_R_Hand'];eb.align_roll(flat)
bpy.ops.object.mode_set(mode='OBJECT')
verts=[];faces=[];classes=[]
def P(a,s,f):return tuple(c+ax*a+side*s+flat*f)
def add(ps):i=len(verts);verts.extend(ps);return i
def tube(path,radii,k,n=8):
 ids=[add([P(a,s+r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n)) for i in range(n)]) for (a,s),r in zip(path,radii)]
 for a,b in zip(ids,ids[1:]):
  for j in range(n):faces.append((a+j,b+j,b+(j+1)%n,a+(j+1)%n));classes.append(k)
 faces.extend([tuple(ids[0]+j for j in reversed(range(n))),tuple(ids[-1]+j for j in range(n))]);classes.extend([k,k])
tube([(-.085,0),(0,0),(.05,0)],[.012,.013,.012],'grip')
tube([(-.085,0),(-.10,0),(-.123,0)],[.012,.025,.009],'gold')
for s in [-1,1]:tube([(.055,0),(.060,.05*s),(.080,.10*s),(.10,.135*s)],[.016,.012,.009,.004],'gold',6)
tube([(.05,0),(.062,0)],[.017,.017],'gold_dark')
rings=[add([P(a,w,0),P(a,0,t),P(a,-w,0),P(a,0,-t)]) for a,w,t in [(.062,.023,.0045),(.10,.025,.0045),(.56,.021,.003),(.735,.014,.0025)]]
for a,b in zip(rings,rings[1:]):
 for j in range(4):faces.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4));classes.append('edge' if j%2==0 else 'blade')
tip=add([P(.785,0,0)])
for j in range(4):faces.append((rings[-1]+j,tip,rings[-1]+(j+1)%4));classes.append('edge')
m=bpy.data.meshes.new('SwordMesh');m.from_pydata(verts,[],faces);m.update()
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
so=bpy.data.objects.new('SwordMesh',m);bpy.context.scene.collection.objects.link(so);so.parent=rig
mod=so.modifiers.new('Armature','ARMATURE');mod.object=rig
so.vertex_groups.new(name='Sword').add(list(range(len(verts))),1,'REPLACE')
m.attributes.new('piece','INT','POINT').data.foreach_set('value',[999]*len(verts))
palette={'grip':(.05,.09,.25,1),'gold':(.70,.38,.055,1),'gold_dark':(.40,.20,.025,1),'blade':(.63,.69,.75,1),'edge':(.85,.9,.94,1)}
for name,color in palette.items():
 mat=bpy.data.materials.new(name);mat.diffuse_color=color;mat.use_nodes=True
 mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=color
 m.materials.append(mat)
for f,k in zip(m.polygons,classes):f.material_index=list(palette).index(k);f.use_smooth=k in ['grip','gold','gold_dark']
so['sword_classes']=json.dumps(classes);so['blade_roll_degrees']=math.degrees(roll)
tris=sum(len(f.vertices)-2 for ob in [body,so] for f in ob.data.polygons)
assert tris<=10000,tris
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v8.blend'))
print('SWORD',len(verts),'vertices',sum(len(f)-2 for f in faces),'tris; combined',tris)
