"""Original mesh construction helpers for the goblin; executed inside Blender."""
import bpy
import bmesh
import math
from mathutils import Vector

def mesh_object(name, vertices, faces, material=None):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm=bmesh.new();bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    if material: data.materials.append(material)
    for poly in data.polygons: poly.use_smooth=True
    return obj

def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj

def apply(obj, modifier):
    active(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)

def ellipsoid(name, center, radii, material=None, rotation=(0,0,0), segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=center)
    obj=bpy.context.object;obj.name=name;obj.scale=radii;obj.rotation_euler=rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:obj.data.materials.append(material)
    for poly in obj.data.polygons:poly.use_smooth=True
    return obj

def loft(name, sections, material=None, sides=32, deform=None, cap=True):
    """Z rings: (z, center_x, center_y, radius_x, radius_y), with optional surface sculpt callback."""
    vertices=[];faces=[]
    for z,cx,cy,rx,ry in sections:
        for i in range(sides):
            a=2*math.pi*i/sides
            v=(cx+rx*math.sin(a),cy-ry*math.cos(a),z)
            vertices.append(deform(v,a) if deform else v)
    for row in range(len(sections)-1):
        for i in range(sides):
            j=row*sides+i;k=row*sides+(i+1)%sides
            faces.append((j,k,k+sides,j+sides))
    if cap:
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((len(sections)-1)*sides+i for i in range(sides)))
    return mesh_object(name,vertices,faces,material)

def tube(name, points, radii, material=None, sides=12, flatten=1.0):
    """Parallel-transport rings avoid arbitrary twists on curved fingers, tendons and metal trim."""
    points=[Vector(p) for p in points];vertices=[];faces=[];u=None
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        if u is None:
            seed=Vector((1,0,0)) if abs(tangent.x)<.8 else Vector((0,1,0))
            u=(seed-tangent*seed.dot(tangent)).normalized()
        else:u=(u-tangent*u.dot(tangent)).normalized()
        v=tangent.cross(u).normalized()
        for j in range(sides):
            a=j*2*math.pi/sides
            vertices.append(tuple(p+radii[i]*(math.cos(a)*u+flatten*math.sin(a)*v)))
    for row in range(len(points)-1):
        for j in range(sides):
            k=row*sides+j;q=row*sides+(j+1)%sides
            faces.append((k,q,q+sides,k+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh_object(name,vertices,faces,material)

def join(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();obj=bpy.context.object;obj.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return obj

def unify(objects,name,voxel=.005,smooth=3,decimate=None):
    obj=join(objects,name);obj.data.remesh_voxel_size=voxel
    bpy.ops.object.voxel_remesh()
    if smooth:
        m=obj.modifiers.new('Blend sculpt masses','SMOOTH');m.factor=.65;m.iterations=smooth;apply(obj,m)
    if decimate:
        m=obj.modifiers.new('Practical sculpt surface','DECIMATE');m.ratio=decimate;apply(obj,m)
    for poly in obj.data.polygons:poly.use_smooth=True
    return obj

def subtract(obj,cutter):
    m=obj.modifiers.new('Carve anatomical opening','BOOLEAN')
    m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;apply(obj,m)
    bpy.data.objects.remove(cutter,do_unlink=True)

def solidify(obj,thickness=.006,bevel=.002):
    m=obj.modifiers.new('Physical material thickness','SOLIDIFY');m.thickness=thickness;apply(obj,m)
    if bevel:
        m=obj.modifiers.new('Worn edge profile','BEVEL');m.width=bevel;m.segments=2;apply(obj,m)
    return obj

def weighted(obj, bone):
    """Explicit rigid-piece attachment preserved through joining and export."""
    group=obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
    obj['attachment_bone']=bone
    return obj

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
