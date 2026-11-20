"""Close the generated armour's empty torso/armholes with a low-poly dark flexible underlayer."""
import bpy,bmesh,json,numpy as np,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/master_pilot.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update();J=json.loads((p/'work/joints_final.json').read_text())['joints']
def sm(t):t=np.clip(t,0,1);return float(t*t*(3-2*t))
def set_w(v,w):
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 total=sum(w.values());assert total>0
 for n,a in w.items():
  if a>1e-6:body.vertex_groups[n].add([v.index],float(a/total),'REPLACE')
# The central codpiece belongs to the pelvis, with a broad transition onto each thigh.
for v in body.data.vertices:
 piece=body.data.attributes['piece'].data[v.index].value;x,y,z=v.co
 if piece not in [0,2] or not .70<z<.94:continue
 sd='L' if piece==0 else 'R';hip=J[sd+'_Thigh'][2];centre=(1-sm(abs(x)/.105))*sm((z-.70)/.065);pel=max(centre,sm((z-(hip-.075))/.15));set_w(v,{f'B_{sd}_Thigh':1-pel,'B_Pelvis':pel})
verts=[];faces=[];weights=[]
levels=[(.82,.115,.085),(.88,.135,.09),(.98,.12,.08),(1.08,.13,.085),(1.18,.15,.095),(1.27,.15,.095),(1.32,.10,.075),(1.35,.07,.075)]
for z,rx,ry in levels:
 if z<1.02:w={'B_Pelvis':1-sm((z-.9)/.12),'B_Spine':sm((z-.9)/.12)}
 else:w={'B_Spine2':1.0}
 for k in range(20):
  a=2*math.pi*k/20;verts.append((rx*math.cos(a),-.025+ry*math.sin(a),z));weights.append(w)
for j in range(len(levels)-1):
 for k in range(20):faces.append((j*20+k,j*20+(k+1)%20,(j+1)*20+(k+1)%20,(j+1)*20+k))
faces.extend([tuple(range(19,-1,-1)),tuple(range((len(levels)-1)*20,len(levels)*20))])
me=bpy.data.meshes.new('UnderArmour');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('UnderArmour',me);bpy.context.scene.collection.objects.link(ob)
for n in {n for w in weights for n in w}:ob.vertex_groups.new(name=n)
for i,w in enumerate(weights):
 for n,a in w.items():
  if a>0:ob.vertex_groups[n].add([i],a,'REPLACE')
objs=[ob]
for sd in 'LR':
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=J[sd+'_UpperArm']);o=bpy.context.object;o.name='ShoulderUndermail_'+sd;o.scale=(.062,.062,.060);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.vertex_groups.new(name=f'B_{sd}_UpperArm').add(list(range(len(o.data.vertices))),1,'REPLACE');objs.append(o)
mat=bpy.data.materials.new('UnderMail');mat.diffuse_color=(.045,.055,.055,1)
for o in objs:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free()
 o.data.materials.append(mat);o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[35]*len(o.data.vertices));uv=o.data.uv_layers.new(name='UVMap')
 for v in uv.data:v.uv=(.5,.5)
 for f in o.data.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in [body,*objs])
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
for v in body.data.vertices:assert abs(sum(g.weight for g in v.groups)-1)<.001
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/master_geometry.blend'))
for name,f in [('Attack',4),('Attack',16),('Running',16)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);common.workbench_clay(bpy.context.scene);common.render_views(str(p/f'review/closed_{name}_{f}'),1.2,.8,views=('three_quarter','left'),resolution=(700,700))
print('FINAL_GEOMETRY',len(body.data.polygons),'triangles')
