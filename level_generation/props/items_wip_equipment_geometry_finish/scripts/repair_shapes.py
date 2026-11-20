"""Repair the remaining structural shapes from the copied meshes; no paid regeneration."""
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from repair_geometry import activate, apply, voxel_union, finish, closed_normals


def mesh(name, vertices, faces):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    closed_normals(obj)
    return obj


def join(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    return objects[0]


def pillow(z, rx, ry, height):
    vertices=[];faces=[];n=48;m=10
    for j in range(m+1):
        phi=math.pi*j/m
        r=max(.002,math.sin(phi))
        for i in range(n):
            a=2*math.pi*i/n
            # Rounded rectangular stacked leather folds, with restrained broad cloth undulation.
            x=math.copysign(abs(math.cos(a))**.6,math.cos(a))*rx*r
            y=math.copysign(abs(math.sin(a))**.6,math.sin(a))*ry*r
            wave=.009*math.sin(a*5+j*.7)*math.sin(phi)
            vertices.append((x,y,z+height*math.cos(phi)+wave))
    for j in range(m):
        for i in range(n):
            k=j*n+i;l=j*n+(i+1)%n
            faces.append((k,l,l+n,k+n))
    faces.extend([tuple(reversed(range(n))),tuple(m*n+i for i in range(n))])
    return mesh('soft_fold',vertices,faces)


def green_hat(original):
    # Keep the source feather; the torn fin-like cloth body needs a new continuous folded crown.
    bm=bmesh.new();bm.from_mesh(original.data);seen=set();parts=[]
    for v in bm.verts:
        if v in seen:continue
        todo=[v];seen.add(v);vs=[]
        while todo:
            a=todo.pop();vs.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b not in seen:seen.add(b);todo.append(b)
        if 15<len(vs)<100:
            fs={f for v in vs for f in v.link_faces};vs=list(vs);index={v:i for i,v in enumerate(vs)}
            parts.append(mesh('retained_feather',[v.co.copy() for v in vs],[tuple(index[v] for v in f.verts) for f in fs]))
    bm.free();bpy.data.objects.remove(original,do_unlink=True)
    vertices=[];faces=[];n=48;m=12
    for j in range(m+1):
        t=j/m
        for i in range(n):
            a=2*math.pi*i/n
            r=max(.006,1-t)
            x=-.18*t-.34*t**3+.45*r*math.cos(a)
            y=.04*t+.32*r*math.sin(a)
            z=.10+.66*t-.51*t**3+.016*math.sin(3*a+.8)*math.sin(math.pi*t)
            vertices.append((x,y,z))
    for j in range(m):
        for i in range(n):
            k=j*n+i;l=j*n+(i+1)%n;faces.append((k,l,l+n,k+n))
    faces.extend([tuple(reversed(range(n))),tuple(m*n+i for i in range(n))])
    crown=mesh('soft_green_crown',vertices,faces)
    # A rolled brim is a physical closed tube; no broad gaps around the band.
    vertices=[];faces=[];n=64;m=8
    for i in range(n):
        a=i*math.tau/n
        for j in range(m):
            b=j*math.tau/m
            vertices.append(((.43+.032*math.cos(b))*math.cos(a),(.31+.032*math.cos(b))*math.sin(a),.09+.055*math.sin(b)+.018*math.cos(a)))
    for i in range(n):
        for j in range(m):faces.append((i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m))
    brim=mesh('rolled_brim',vertices,faces)
    obj=join([crown,brim]+parts);voxel_union(obj,.006)
    return obj


def wreath(original):
    bm=bmesh.new();bm.from_mesh(original.data);seen=set();parts=[]
    for v in bm.verts:
        if v in seen:continue
        stack=[v];seen.add(v);vs=[]
        while stack:
            a=stack.pop();vs.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b not in seen:seen.add(b);stack.append(b)
        if 20<=len(vs)<=110:
            fs={f for v in vs for f in v.link_faces};vs=list(vs);index={v:i for i,v in enumerate(vs)}
            parts.append(([v.co.copy() for v in vs],[tuple(index[v] for v in f.verts) for f in fs]))
    bm.free();assert len(parts)>3
    bpy.data.objects.remove(original,do_unlink=True)
    bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=8,major_radius=.35,minor_radius=.023,location=(0,0,.055))
    band=bpy.context.object;objects=[band]
    for i in range(14):
        vs,fs=parts[i%len(parts)];centre=sum(vs,Vector())/len(vs)
        extent=max(max(v[k] for v in vs)-min(v[k] for v in vs) for k in range(3))
        a=math.tau*i/14
        rotation=Matrix.Rotation(a,4,'Z')@Matrix.Rotation(math.radians(62),4,'X')
        place=Vector((.35*math.cos(a),.35*math.sin(a),.085))
        points=[rotation@(v-centre)*(.24/extent)+place for v in vs]
        objects.append(mesh('retained_leaf_'+str(i),points,fs))
        if i%2==0:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.027,location=(.33*math.cos(a),.33*math.sin(a),.12))
            objects.append(bpy.context.object)
    return join(objects)


def crescent(obj):
    closed_normals(obj)
    bvh=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
    hit,normal,_,_=bvh.ray_cast(Vector((.17,.17,2)),Vector((0,0,-1)))
    assert hit is not None
    points=[];radius=.13;offset=.065;inner=(radius**2-offset**2)**.5
    for i in range(25):
        a=math.radians(60+240*i/24);points.append((radius*math.cos(a),radius*math.sin(a)))
    for i in range(1,24):
        a=math.radians(270-180*i/24);points.append((offset+inner*math.cos(a),inner*math.sin(a)))
    vertices=[(x,y,z) for z in [0,.018] for x,y in points];n=len(points)
    faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    clasp=mesh('raised_crescent_clasp',vertices,faces)
    # Seat the back of the brooch against its supporting fold.
    normal=normal if normal.z>0 else -normal
    rotation=Vector((0,0,1)).rotation_difference(normal)
    for v in clasp.data.vertices:v.co=rotation@v.co+hit+normal*.002
    return join([obj,clasp])


def mask_eyes(obj):
    voxel_union(obj,.007)
    for x in [-.23,.03]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=1,depth=.44,location=(x,-.34,.605),rotation=(math.pi/2,0,0))
        cut=bpy.context.object;cut.scale=(.105,.078,1)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        mod=obj.modifiers.new('Actual open eye socket','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
        apply(obj,mod);bpy.data.objects.remove(cut,do_unlink=True)
    return obj


def main():
    for icon in sys.argv[sys.argv.index('--')+1:]:
        name='equipment_'+icon
        bpy.ops.wm.open_mainfile(filepath=str(P/'references/scenes'/f'{name}.blend'))
        obj=bpy.data.objects[name]
        for other in list(bpy.context.scene.objects):
            if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
        activate(obj)
        if icon in ['item124','item125']:
            for v in obj.data.vertices:v.co.z*=.48
            obj=join([obj,pillow(.065,.46,.34,.055),pillow(.13,.44,.32,.06)])
            voxel_union(obj,.006)
        elif icon=='6hat1':obj=green_hat(obj)
        elif icon=='6crown1':obj=wreath(obj)
        elif icon=='7item344':obj=mask_eyes(obj)
        elif icon=='7item348':
            from thicken_trial import thicken
            obj=thicken(obj,.012)
            voxel_union(obj,.004)
            obj=crescent(obj)
        else:raise ValueError(icon)
        finish(obj,name,3200)


if __name__=='__main__':main()
