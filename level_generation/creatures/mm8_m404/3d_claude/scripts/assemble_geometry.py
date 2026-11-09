"""Assemble the clean three-finger body with the independently reviewed multiview head."""
import bpy,bmesh,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/front_v3_parts.blend'))
for o in list(bpy.data.objects):
    if o.type!='MESH' or (int(o.name[1:])>=10 and o.name!='P13') or o.name=='P05':
        bpy.data.objects.remove(o,do_unlink=True)
body=bpy.data.objects['P01'];bm=bmesh.new();bm.from_mesh(body.data)
cut=1.555
cross=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,cut),plane_no=(0,0,1),clear_outer=True)
ring=[v for v in bm.verts if abs(v.co.z-cut)<1e-5]
dst=np.mean([v.co[:] for v in ring],axis=0)
dst_points=np.array([v.co[:] for v in ring]);radius=(dst_points.max(0)-dst_points.min(0))[:2]/2
for v in bm.verts:
    weight=max(0,min(1,(v.co.z-1.48)/(cut-1.48)))
    v.co.x=dst[0]+(v.co.x-dst[0])*(1-.35*weight)
    v.co.y=dst[1]+(v.co.y-dst[1])*(1-.10*weight)
radius*=np.array([.65,.9])
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-cut)<1e-5 for v in e.verts)],sides=0)
bm.to_mesh(body.data);bm.free()
with bpy.data.libraries.load(str(p/'work/mv_v2_dense_parts.blend'),link=False) as (source,target):target.objects=['P00']
head=target.objects[0];bpy.context.collection.objects.link(head);head.name='Head'
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,1.61),plane_no=(0,0,1),clear_inner=True)
ring=[v for v in bm.verts if abs(v.co.z-(1.61))<1e-5]
src=np.mean([v.co[:] for v in ring],axis=0)
shift=Vector((float(dst[0]-src[0]),float(dst[1]-src[1]),0))
for v in bm.verts:v.co+=shift
boundary=[e for e in bm.edges if e.is_boundary]
extruded=bmesh.ops.extrude_edge_only(bm,edges=boundary)
verts=[v for v in extruded['geom'] if isinstance(v,bmesh.types.BMVert)]
for v in verts:
    d=np.array(v.co[:2])-dst[:2];angle=np.arctan2(d[1]/radius[1],d[0]/radius[0])
    v.co.x=float(dst[0]+radius[0]*np.cos(angle));v.co.y=float(dst[1]+radius[1]*np.sin(angle));v.co.z=cut-.01
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
# The head is rigid above its concealed collar junction; weight before silhouette reduction.
g=head.vertex_groups.new(name='B_Head');g.add(list(range(len(head.data.vertices))),1,'REPLACE')
for o in bpy.data.objects:o.select_set(o==head)
bpy.context.view_layer.objects.active=head
tri=sum(len(f.vertices)-2 for f in head.data.polygons)
m=head.modifiers.new('Head silhouette budget','DECIMATE');m.ratio=3200/tri;bpy.ops.object.modifier_apply(modifier=m.name)
head.data.materials.clear()
mat=bpy.data.materials.new('Head clay');mat.diffuse_color=(.4,.55,.7,1);head.data.materials.append(mat)
for f in head.data.polygons:f.use_smooth=True
print('HEAD',tri,'->',len(head.data.polygons),'shift',list(shift))
# Stable piece ids retain garment/skin ownership through joining.
parts={'P00':0,'P01':0,'P02':1,'P03':0,'P04':0,'P06':2,'P07':3,'P08':4,'P09':5,'P13':6,'Head':7}
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    a=o.data.attributes.new('piece','INT','POINT')
    for x in a.data:x.value=parts[o.name]
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/assembled_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/assembled'),.95,2.15,views=('front','left','back','three_quarter'),resolution=(800,900))
common.render_views(str(p/'review/assembled_head'),1.69,.50,views=('front','left'),resolution=(600,600),target=(float(dst[0]),float(dst[1])))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
# Provisional neutral texture satisfies the rigging service; final UVs are created after deformation gates.
body.data.materials.clear();mat=bpy.data.materials.new('Rig provisional');mat.use_nodes=True
im=bpy.data.images.new('Rig provisional',width=2,height=2);im.generated_color=(.55,.55,.55,1);im.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'export/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
assert len(body.data.vertices)>5000
json.dump({'head_source':'multiview_geometry_v2 dense','body_source':'front_geometry_v3','head_translation':list(shift),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'pieces':parts},open(p/'work/assembly.json','w'),indent=2)
