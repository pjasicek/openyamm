"""Clean the new pfem Smart Topology mesh before rigging; retain face/hand density."""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
import numpy as np
import sys
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
# The generated split nape tails contradict every native rear view.
hair=parts['P02']
bm=bmesh.new(); bm.from_mesh(hair.data)
drop=[v for v in bm.verts if (v.co.z<1.455 and v.co.y>0.073) or (abs(v.co.x+.006)<.06 and v.co.y<-.02 and 1.4<v.co.z<1.554)]
bmesh.ops.delete(bm,geom=drop,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(hair.data);bm.free()
# Close only small face openings (eyes, nose, lips), retaining the neck and scalp boundaries.
for n in ('P16','P17'):
    bpy.data.objects.remove(parts.pop(n),do_unlink=True)
face=parts['P01'];bm=bmesh.new();bm.from_mesh(face.data)
edges=[e for e in bm.edges if e.is_boundary and all(v.co.y<-.025 and 1.40<v.co.z<1.55 for v in e.verts)]
res=bmesh.ops.holes_fill(bm,edges=edges,sides=0)
bmesh.ops.triangulate(bm,faces=res['faces'])
# Calm the small folded eyelid/nostril surfaces without changing the face silhouette.
seeds=[(Vector((-.035,-.074,1.526)),.026),(Vector((.018,-.074,1.527)),.026),(Vector((-.008,-.10,1.479)),.016)]
for _ in range(6):
    moves={}
    for v in bm.verts:
        w=max((max(0.,1-(v.co-c).length/r) for c,r in seeds),default=0)*.42
        if w and v.link_edges and not any(e.is_boundary for e in v.link_edges):
            moves[v]=v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),w)
    for v,co in moves.items():v.co=co
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(face.data);bm.free()
# One compact plait with a low tie and soft tuft, tucked against the nape.
verts=[];faces=[]
def tube(rings):
    start=len(verts);n=len(rings[0])
    for ring in rings:verts.extend(ring)
    for i in range(len(rings)-1):
        for j in range(n):
            a=start+i*n+j;b=start+i*n+(j+1)%n
            faces.append((a,b,b+n,a+n))
    faces.append(tuple(start+j for j in reversed(range(n))))
    last=start+(len(rings)-1)*n;faces.append(tuple(last+j for j in range(n)))
def path(z):
    return Vector((-.006,.081+.008*max(0,min(1,(1.46-z)/.08)),z))
for strand in range(3):
    rings=[]
    for i in range(19):
        t=i/18;z=1.47-.105*t;th=t*math.pi*4+strand*2*math.pi/3
        spread=.011*(1-.25*t);c=path(z)+Vector((spread*math.sin(th),spread*.65*math.sin(2*th),0))
        r=.0125*(1-.22*t)
        rings.append([c+Vector((math.cos(j*math.tau/6)*r,math.sin(j*math.tau/6)*r,0)) for j in range(6)])
    tube(rings)
tube([[path(z)+Vector((math.cos(a*math.tau/10)*r,math.sin(a*math.tau/10)*r,0)) for a in range(10)]
      for z,r in ((1.370,.016),(1.366,.018),(1.356,.018),(1.353,.016))])
rings=[]
for i in range(9):
    t=i/8;z=1.356-.047*t;r=.016*(.85+.55*math.sin(math.pi*t))*(1-.75*t**3)
    rings.append([path(z)+Vector((math.cos(a*math.tau/10)*r*(1+.13*math.cos(3*a*math.tau/10+t*4)),math.sin(a*math.tau/10)*r,0)) for a in range(10)])
tube(rings)
me=bpy.data.meshes.new('Braid');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('P19',me);bpy.context.collection.objects.link(ob);parts['P19']=ob
for name,ob in parts.items():
    attr=ob.data.attributes.new('piece','INT','POINT')
    attr.data.foreach_set('value',[int(name[1:])]*len(ob.data.vertices))
    for face in ob.data.polygons:face.use_smooth=True
    ob.select_set(True)
bpy.context.view_layer.objects.active=parts['P00']
bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body'
me=body.data
# Separate skirt ownership by its actual waist height, without splitting its surface.
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
for v in me.vertices:
    if pv[v.index]==0 and v.co.z<1.07:pv[v.index]=100
me.attributes['piece'].data.foreach_set('value',pv)
co=np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.context.scene['pfem_piece_roles']=json.dumps({'dress':0,'skirt':100,'head_skin':1,'hair':2,'right_hand':3,'left_hand':4,'right_arm':11,'left_arm':9,'right_leg':8,'left_leg':10,'right_shoe':[5,15],'left_shoe':[6,14],'headband':7,'belt':[12,13,18],'braid':19})
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/clean'),.83,1.80,views=('front','left','back'),resolution=(600,900))
common.render_views(str(p/'review/clean_head'),1.49,.35,views=('front','left','back'),resolution=(600,600))
# Provisional flat texture for the rig service; final texturing follows deformation review.
body.data.materials.clear()
mat=bpy.data.materials.new('RigPreview');mat.use_nodes=True
im=bpy.data.images.new('RigPreview',width=8,height=8)
im.generated_color=(.7,.7,.7,1)
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
for poly in me.polygons:poly.material_index=0
if not me.uv_layers:me.uv_layers.new(name='UVMap')
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
print('CLEAN tris',sum(len(f.vertices)-2 for f in me.polygons),'new braid tris',sum(len(f)-2 for f in faces))
