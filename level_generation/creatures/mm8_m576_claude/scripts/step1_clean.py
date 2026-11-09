"""Remove invented torso spines, seat the crest, close visible shells, and prepare rig upload."""
from pathlib import Path
import sys,json,math
import bpy,bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
for obj in list(bpy.data.objects):
    if obj.name in ('P10','P11','P12'):bpy.data.objects.remove(obj,do_unlink=True)
body=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(body.data)
co=np.array([v.co[:] for v in bm.verts]);cx=-.007
removed=[]
for side in ('back','front'):
    verts=[]
    for v in bm.verts:
        x,y,z=v.co
        if abs(x-cx)>.025 or not 1.00<z<1.49:continue
        flank=co[(np.abs(co[:,0]-cx)>.030)&(np.abs(co[:,0]-cx)<.065)&(np.abs(co[:,2]-z)<.025)]
        if side=='back':
            flank=flank[flank[:,1]>.025]
            bad=y>.025
        else:
            flank=flank[flank[:,1]<-.04]
            bad=y<-.04
        if bad:verts.append(v)
    removed.append((side,len(verts)))
    assert verts,side
    bmesh.ops.delete(bm,geom=verts,context='VERTS')
# The removed narrow roots leave skin loops; beauty triangulation bridges neighbouring ring vertices.
boundary=[e for e in bm.edges if e.is_boundary]
res=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
newfaces=res['faces']
print('PATCH loops',len(newfaces),[len(f.verts) for f in newfaces])
bmesh.ops.triangulate(bm,faces=newfaces,quad_method='BEAUTY',ngon_method='BEAUTY')
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
assert not any(e.is_boundary for e in bm.edges)
bm.to_mesh(body.data);bm.free()
# The separate crest cap was coincident with the scalp; move its embedded surface just outside the skin.
bm=bmesh.new();bm.from_mesh(body.data);tree=BVHTree.FromBMesh(bm)
crest=bpy.data.objects['P01'];moved=0
for v in crest.data.vertices:
    hit,normal,_,distance=tree.find_nearest(v.co)
    if distance<.009 and (v.co-hit).dot(normal)<.0025:
        v.co=hit+normal*.0025;moved+=1
bm.free()
# The single-view return omitted the native crossed chest/back straps and enlarged its centre inset.
bpy.data.objects.remove(bpy.data.objects['P02'],do_unlink=True)
bpy.data.objects.remove(bpy.data.objects['P09'],do_unlink=True)
bm=bmesh.new();bm.from_mesh(body.data);skin=BVHTree.FromBMesh(bm)
def surface(x,z,front):
    origin=Vector((x,-1 if front else 1,z));direction=Vector((0,1 if front else -1,0))
    hit,normal,_,_=skin.ray_cast(origin,direction)
    assert hit is not None,(x,z,front)
    return hit+Vector((0,-.004 if front else .004,0))
for part,front in ((10,True),(11,False)):
    verts=[];faces=[]
    for diagonal in (-1,1):
        a=Vector((cx-.14*diagonal,1.38));b=Vector((cx+.10*diagonal,1.13))
        tangent=(b-a).normalized();side=Vector((-tangent.y,tangent.x))*.018
        base=len(verts)
        for i in range(13):
            c=a.lerp(b,i/12)
            for sign in (-1,1):
                x,z=c+side*sign;v=surface(x,z,front)
                if diagonal==1:v.y+=-.0025 if front else .0025
                verts.append(tuple(v))
        faces.extend((base+2*i,base+2*i+1,base+2*i+3,base+2*i+2) for i in range(12))
    mesh=bpy.data.meshes.new('CrossedStraps');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(f'P{part:02d}',mesh);bpy.context.collection.objects.link(obj)
# A fitted continuous collar replaces the torn, floating generated collar.
verts=[];faces=[];count=40;rows=9
for i in range(count):
    angle=2*math.pi*i/count;radial=Vector((math.cos(angle),math.sin(angle),0))
    for row in range(rows):
        z=1.425+(1.372-.055*max(0,-math.sin(angle))**3-1.425)*row/(rows-1)
        origin=Vector((cx,0,z))+radial
        hit,normal,_,_=skin.ray_cast(origin,-radial)
        assert hit is not None,(i,z)
        verts.append(tuple(hit+normal*.006))
for i in range(count):
    j=(i+1)%count
    for row in range(rows-1):faces.append((rows*i+row,rows*j+row,rows*j+row+1,rows*i+row+1))
mesh=bpy.data.meshes.new('Collar');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('P02',mesh);bpy.context.collection.objects.link(obj)
centre=surface(cx,1.245,True);centre.y-=.012
verts=[centre+Vector(v) for v in ((0,0,.045),(.012,0,0),(0,0,-.045),(-.012,0,0),(0,-.005,0),(0,.003,0))]
mesh=bpy.data.meshes.new('SternumInset');mesh.from_pydata(verts,[],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]);mesh.update()
obj=bpy.data.objects.new('P09',mesh);bpy.context.collection.objects.link(obj)
bm.free()
for obj in bpy.data.objects:
    obj.select_set(False)
for part in (1,2,3,4,5,6,10,11):
    obj=bpy.data.objects[f'P{part:02d}'];obj.select_set(True);bpy.context.view_layer.objects.active=obj
    solid=obj.modifiers.new('Visible shell thickness','SOLIDIFY');solid.thickness=.002;solid.offset=0
    bpy.ops.object.modifier_apply(modifier=solid.name);obj.select_set(False)
labels={0:'skin_and_limb_fins',1:'head_crest',2:'collar',3:'left_pauldron',4:'right_pauldron',5:'left_upperarm_plate',6:'right_upperarm_plate',7:'right_eye',8:'left_eye',9:'chest_inset',10:'front_harness',11:'back_harness'}
parts=[o for o in bpy.data.objects if o.type=='MESH']
for obj in parts:
    part=int(obj.name[1:]);obj.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[part]*len(obj.data.vertices))
    colour=(.045,.24,.16,1) if part in (0,1) else (.13,.15,.14,1) if part in (3,4,5,6,10,11) else (.40,.52,.42,1) if part==2 else (.025,.03,.25,1) if part==9 else (.45,.48,.05,1)
    mat=bpy.data.materials.new(labels[part]);mat.use_nodes=True;mat.diffuse_color=colour
    shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.8
    im=bpy.data.images.new('Provisional_'+labels[part],8,8);im.generated_color=colour;im.pack()
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    obj.data.materials.clear();obj.data.materials.append(mat)
    if not obj.data.uv_layers:
        uv=obj.data.uv_layers.new(name='ProvisionalUV')
        for loop in obj.data.loops:
            v=obj.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x/2+.5,v.z/1.7)
    for face in obj.data.polygons:face.use_smooth=True
    obj.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
assert not body.data.validate()
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
(p/'work/parts_labels.json').write_text(json.dumps(labels,indent=2))
(p/'review/geometry_cleanup.json').write_text(json.dumps({'removed_vertices':removed,'crest_vertices_seated':moved,'closed_visible_shells':[1,2,3,4,5,6,10,11]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/clean_v2'),.85,1.95,views=('front','left','back','three_quarter'),resolution=(750,1000))
common.render_views(str(p/'review/clean_head'),1.55,.38,views=('front','left'),resolution=(650,650))
print('CLEAN',removed,'seated',moved,'triangles',sum(len(f.vertices)-2 for f in body.data.polygons))
