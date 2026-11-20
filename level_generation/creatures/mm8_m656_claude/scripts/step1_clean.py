"""Repair skirt overlap and missing cheek guards, retain part labels, export a provisional textured rig input."""
from pathlib import Path
import bpy, bmesh, json, sys
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
# The continuous backing intersected the separately generated tassets and flickered through them.
backing=bpy.data.objects['P16']
for v in backing.data.vertices:
 v.co.x=-0.006+(v.co.x+0.006)*0.94
 v.co.y=0.014+(v.co.y-0.014)*0.91
# Preserve each tasset's envelope while replacing its folded, nearly coincident triangle surfaces.
for index in range(43,83):
 obj=bpy.data.objects[f'P{index:02d}'];co=np.array([v.co[:] for v in obj.data.vertices]);center=co.mean(0)
 radial=np.array([(center[0]+.006)/(.18*.18),(center[1]-.014)/(.14*.14),0.]);radial/=np.linalg.norm(radial)
 tangent=np.array([-radial[1],radial[0],0.]);t=(co-center)@tangent;r=(co-center)@radial;z=co[:,2]
 slope,offset=np.polyfit(z-center[2],r,1);verts=[]
 for depth in [-.002,.002]:
  for height in [z.min(),z.max()]:
   for along in [t.min(),t.max()]:
    v=center+tangent*along+radial*(slope*(height-center[2])+offset+.006+depth)
    v[2]=height;verts.append(tuple(v))
 mesh=bpy.data.meshes.new(obj.name+'_plate')
 mesh.from_pydata(verts,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(mesh);bm.free()
 obj.data=mesh
 assert len(mesh.polygons)==6
# Close the small unintended armpit opening; larger garment openings remain covered by neighbouring parts.
bm=bmesh.new();bm.from_mesh(bpy.data.objects['P00'].data)
edges=[e for e in bm.edges if e.is_boundary and all(1.23<v.co.z<1.26 and v.co.x<-.16 for v in e.verts)]
assert len(edges)==5
bmesh.ops.holes_fill(bm,edges=edges,sides=5)
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(bpy.data.objects['P00'].data);bm.free()
# Model the native helmet's side guards as curved plates fitted over the ears and cheeks.
for index,sign in [(84,-1),(85,1)]:
 upper=[(-.051,1.558,.079),(-.005,1.568,.100),(.055,1.570,.095),(.112,1.558,.057)]
 lower=[(-.041,1.494,.079),(-.005,1.483,.094),(.055,1.500,.088),(.100,1.512,.059)]
 verts=[(sign*x,y,z) for row in [upper,lower] for y,z,x in row]
 faces=[(i,i+1,i+5,i+4) for i in range(3)]
 mesh=bpy.data.meshes.new('CheekGuard');mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(f'P{index:02d}',mesh);bpy.context.collection.objects.link(obj)
 for o in bpy.data.objects:o.select_set(o==obj)
 bpy.context.view_layer.objects.active=obj
 solid=obj.modifiers.new('Plate thickness','SOLIDIFY');solid.thickness=.004
 bpy.ops.object.modifier_apply(modifier=solid.name)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(mesh);bm.free()
 assert len(mesh.polygons)>3
labels={0:'cuirass_sleeves',1:'head_neck',2:'right_glove',3:'left_glove',4:'trousers',5:'helmet',
6:'left_boot',7:'right_boot',8:'lower_hair',9:'left_pauldron',10:'right_pauldron',11:'left_bracer',
12:'belt',13:'right_bracer',14:'left_upperarm_plate',15:'right_upperarm_plate',16:'skirt_backing',
17:'right_horn',18:'left_horn',19:'upper_hair',20:'left_elbow',21:'right_eye',22:'left_eye',23:'right_elbow',
24:'buckle',25:'right_boot_cuff',26:'left_boot_cuff',27:'mouth',28:'right_upper_spike',29:'left_upper_spike',
30:'left_lower_spike',31:'right_lower_spike',84:'right_cheek_guard',85:'left_cheek_guard'}
materials={}
colours={'armour':(.10,.11,.055,1),'cloth':(.025,.13,.05,1),'steel':(.12,.13,.14,1),
'leather':(.035,.022,.015,1),'skin':(.55,.32,.19,1),'hair':(.09,.042,.015,1),'gold':(.45,.29,.065,1),'tan':(.23,.12,.045,1)}
for name,colour in colours.items():
 mat=bpy.data.materials.new('Mercenary_'+name);mat.use_nodes=True;mat.diffuse_color=colour
 shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.8
 im=bpy.data.images.new('Provisional_'+name,8,8);im.generated_color=colour;im.pack()
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
 mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);materials[name]=mat
parts=[o for o in bpy.data.objects if o.type=='MESH']
for obj in parts:
 part=int(obj.name[1:]);labels.setdefault(part,'tasset' if part>=43 else 'belt_or_boot_detail')
 kind=('skin' if part==1 else 'hair' if part in [8,19] else 'cloth' if part==4 else
 'leather' if part in [2,3,6,7,12] else 'steel' if part in [5,11,13,21,22,84,85] else
 'gold' if part in [24,32,34,35,36,37] else 'tan' if part in [17,18,20,23,25,26,28,29,30,31] else 'armour')
 obj.data.materials.clear();obj.data.materials.append(materials[kind])
 obj.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[part]*len(obj.data.vertices))
 for face in obj.data.polygons:face.use_smooth=not (43<=part<=82)
 if not obj.data.uv_layers:
  uv=obj.data.uv_layers.new(name='ProvisionalUV')
  for loop in obj.data.loops:
   v=obj.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x/2+.5,v.z/1.7)
for obj in bpy.data.objects:obj.select_set(obj in parts)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body'
assert not body.data.validate()
co=[x for v in body.data.vertices for x in v.co]
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co)
(p/'work/parts_labels.json').write_text(json.dumps(labels,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',
 export_animations=False,export_skins=False,export_attributes=False)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/clean_v1'),.85,1.88,views=('front','left','back','three_quarter'),resolution=(600,900))
common.render_views(str(p/'review/clean_head'),1.54,.43,views=('front','left','three_quarter'),resolution=(500,500))
print('CLEAN triangles',sum(len(f.vertices)-2 for f in body.data.polygons))
