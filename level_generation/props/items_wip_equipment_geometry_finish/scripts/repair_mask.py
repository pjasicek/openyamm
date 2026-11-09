"""Retain the source knot/ties; rebuild two open eye rims and a continuous thick leather strap."""
import math,sys
from pathlib import Path
import bmesh,bpy
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from repair_geometry import closed_normals,finish,voxel_union
from repair_shapes import mesh,join
from repair_boots import bar


def eye(cx):
    n=48;verts=[];faces=[]
    for back in [False,True]:
        for inner in [False,True]:
            rx,rz=(.10,.063) if inner else (.177,.14)
            for i in range(n):
                a=math.tau*i/n
                verts.append((cx+rx*math.cos(a),-.38+.032*math.cos(a)**2+(.022 if back else 0),.605+rz*math.sin(a)))
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                  (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    return mesh('moulded_open_eye',verts,faces)


def strap():
    n=56;verts=[];faces=[]
    for i in range(n):
        a=math.radians(-45+270*i/(n-1))
        for radial,z in [(-.009,-.045),(.009,-.045),(.009,.045),(-.009,.045)]:
            verts.append((-.06+(.51+radial)*math.cos(a),.02+(.38+radial)*math.sin(a),.55+.015*math.sin(a)+z))
    for i in range(n-1):
        for j in range(4):faces.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
    faces += [(3,2,1,0),tuple((n-1)*4+j for j in range(4))]
    return mesh('continuous_leather_strap',verts,faces)


def rest(obj):
    obj.data.calc_loop_triangles();points=[obj.matrix_world@v.co for v in obj.data.vertices]
    volume=0;weighted=Vector()
    for tri in obj.data.loop_triangles:
        a,b,c=[points[i] for i in tri.vertices];v=a.dot(b.cross(c))/6
        volume+=v;weighted+=(a+b+c)/4*v
    assert volume>0
    centre=weighted/volume;bm=bmesh.new();vs=[bm.verts.new(v) for v in points]
    bmesh.ops.convex_hull(bm,input=vs,use_existing_faces=False);bm.normal_update();candidates=[]
    for f in bm.faces:
        if f.normal.z>=-.5:continue
        a,b,c=[v.co for v in f.verts[:3]];projected=centre-f.normal*(centre-a).dot(f.normal)
        if (closest_point_on_tri(projected,a,b,c)-projected).length<1e-5:candidates.append(f.normal.copy())
    assert candidates,'No stable mask ground support'
    down=Vector((0,0,-1));normal=min(candidates,key=lambda n:n.angle(down));rotation=normal.rotation_difference(down)
    for v in obj.data.vertices:v.co=rotation@v.co
    bm.free()


def main():
    name='equipment_7item344'
    bpy.ops.wm.open_mainfile(filepath=str(P/'references/scenes'/f'{name}.blend'))
    original=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(original.data);seen=set();parts=[]
    for v in bm.verts:
        if v in seen:continue
        stack=[v];seen.add(v);vs=[]
        while stack:
            a=stack.pop();vs.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b not in seen:seen.add(b);stack.append(b)
        if 12<len(vs)<160 and max(v.co.z for v in vs)<.4:
            fs={f for v in vs for f in v.link_faces};vs=list(vs);index={v:i for i,v in enumerate(vs)}
            parts.append(mesh('retained_knot_and_tie',[v.co+Vector((0,0,.25)) for v in vs],[tuple(index[v] for v in f.verts) for f in fs]))
    bm.free();assert parts
    for other in list(bpy.context.scene.objects):
        if other not in parts:bpy.data.objects.remove(other,do_unlink=True)
    parts += [eye(-.23),eye(.05),strap(),bar((-.09,-.37,.62),(.07,.045,.16)),
              bar((.263,-.29,.55),(.075,.18,.08)),bar((-.408,-.29,.55),(.06,.18,.08))]
    obj=join(parts);closed_normals(obj);voxel_union(obj,.003)
    from mathutils.bvhtree import BVHTree
    bvh=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
    for x in [-.23,.05]:
        assert bvh.ray_cast(Vector((x,-1,.605)),Vector((0,1,0)),.8)[0] is None, 'Eye opening capped'
        assert bvh.ray_cast(Vector((x+.14,-1,.605)),Vector((0,1,0)),.8)[0] is not None, 'Eye rim missing'
    rest(obj);finish(obj,name,3200)


if __name__=='__main__':main()
