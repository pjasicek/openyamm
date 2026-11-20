"""Local, icon-specific repairs; preserve the copied source scenes and rebuild exact painting guides."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import codex_texture as paint


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply(obj, modifier):
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)



def split_pinched_fans(bm):
    """Separate surface fans that touch along one edge; retain every real surface face."""
    rims=[f for f in bm.faces if any(e.is_boundary for e in f.edges)
          and any(len(e.link_faces)>2 for e in f.edges)
          and all(len(e.link_faces)!=2 for e in f.edges)]
    if rims:bmesh.ops.delete(bm,geom=rims,context='FACES')
    if not any(len(e.link_faces)>2 for e in bm.edges):return bm
    bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    replacement=bmesh.new();mapping={}
    for v in bm.verts:
        seen=set()
        for f in v.link_faces:
            if f in seen:continue
            todo=[f];seen.add(f);fan=[]
            while todo:
                face=todo.pop();fan.append(face)
                for edge in face.edges:
                    if v not in edge.verts or len(edge.link_faces)!=2:continue
                    for other in edge.link_faces:
                        if other not in seen:seen.add(other);todo.append(other)
            new=replacement.verts.new(v.co)
            for face in fan:mapping[face,v]=new
    seen_faces=set()
    for f in bm.faces:
        vertices=[mapping[f,v] for v in f.verts]
        key=frozenset(vertices)
        if len(key)<3 or key in seen_faces:continue
        seen_faces.add(key)
        face=replacement.faces.new(vertices)
        face.material_index=f.material_index;face.smooth=f.smooth
    bm.free()
    return replacement


def closed_normals(obj, fill=True):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm=split_pinched_fans(bm)
    # Voxel/decimation can leave isolated flat triangle pairs; they are not physical leather or hardware.
    seen=set();discard=[]
    for f in bm.faces:
        if f in seen:continue
        todo=[f];seen.add(f);group=[]
        while todo:
            face=todo.pop();group.append(face)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other not in seen:seen.add(other);todo.append(other)
        if len(group)<=4:
            vertices=list({v for face in group for v in face.verts})
            centre=sum((v.co for v in vertices),Vector())/len(vertices)
            volume=0
            for face in group:
                vs=[v.co-centre for v in face.verts]
                volume+=sum(vs[0].dot(vs[j].cross(vs[j+1]))/6 for j in range(1,len(vs)-1))
            if abs(volume)<1e-11:discard.extend(group)
    if discard:bmesh.ops.delete(bm,geom=discard,context='FACES')
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.00000001)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    if fill:
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    seen=set()
    for face in bm.faces:
        if face in seen:continue
        stack=[face];seen.add(face);group=[]
        while stack:
            f=stack.pop();group.append(f)
            for e in f.edges:
                for other in e.link_faces:
                    if other not in seen:seen.add(other);stack.append(other)
        volume=0
        for f in group:
            vs=[v.co for v in f.verts]
            volume += sum(vs[0].dot(vs[j].cross(vs[j+1]))/6 for j in range(1,len(vs)-1))
        if volume<0:bmesh.ops.reverse_faces(bm,faces=group)
    bm.to_mesh(obj.data)
    bm.free()


def voxel_union(obj, size=.009):
    closed_normals(obj)
    obj.data.remesh_voxel_size = size
    activate(obj)
    bpy.ops.object.voxel_remesh()
    smooth = obj.modifiers.new('Relax repaired seams', 'SMOOTH')
    smooth.factor = .45
    smooth.iterations = 3
    apply(obj, smooth)


def cavity(obj, centre, radii, bottom, top, depth_axis='Z'):
    # Taper the deep recess to leave a sound toe/sole or crown above the wear opening.
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=.72, radius2=1,
                                    depth=top-bottom, location=(0, 0, (top+bottom)/2))
    cut = bpy.context.object
    cut.scale.x, cut.scale.y = radii
    cut.location.x, cut.location.y = centre
    if depth_axis == 'Y':
        cut.rotation_euler.x = math.pi/2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mod = obj.modifiers.new('Real open interior', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cut
    apply(obj, mod)
    bpy.data.objects.remove(cut, do_unlink=True)


def normalize(obj):
    activate(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z))
    for v in obj.data.vertices:
        v.co -= shift


def finish(obj, name, budget=3000):
    closed_normals(obj)
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
    bm.to_mesh(obj.data);bm.free()
    obj.data.calc_loop_triangles()
    if len(obj.data.loop_triangles) > budget:
        mod = obj.modifiers.new('Silhouette budget', 'DECIMATE')
        mod.ratio = budget / len(obj.data.loop_triangles)
        mod.use_collapse_triangulate = True
        apply(obj, mod)
    closed_normals(obj)
    normalize(obj)
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bm = bmesh.new();bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges), (name, 'nonmanifold edges', [(len(e.link_faces), [list(v.co) for v in e.verts]) for e in bm.edges if not e.is_manifold][:8])
    assert all(f.calc_area() > 1e-12 for f in bm.faces)
    bm.free()
    obj.name = name
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/codex_tex'/f'{name}.blend'))
    # A temporary untextured GLB is for the clay gate only.
    activate(obj)
    clay=P/'work/clay';clay.mkdir(exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(clay/f'{name}_export.glb'), export_format='GLB', use_selection=True)
    paint.guides(name)


def main():
    icons=sys.argv[sys.argv.index('--')+1:]
    audit=json.loads((P/'receipts/scene_audit.json').read_text())
    for icon in icons:
        name='equipment_'+icon
        bpy.ops.wm.open_mainfile(filepath=str(P/'references/scenes'/f'{name}.blend'))
        obj=bpy.data.objects[name]
        for other in list(bpy.context.scene.objects):
            if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
        activate(obj)
        if icon in ['6boots1','6boots5']:
            # Back the torn shaft panels with continuous leather before carving their interiors.
            cores=[]
            for upper in audit[icon]['upper_boots']:
                low,high=upper['bounds']
                cx,cy=(low[0]+high[0])/2,(low[1]+high[1])/2
                top=high[2]-.045
                bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.78,radius2=1,depth=top-.28,
                    location=(cx,cy,(top+.28)/2))
                core=bpy.context.object;core.scale.x=(high[0]-low[0])*.43;core.scale.y=(high[1]-low[1])*.43
                bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);cores.append(core)
            activate(obj)
            for core in cores:core.select_set(True)
            bpy.ops.object.join()
            voxel_union(obj)
            for upper in audit[icon]['upper_boots']:
                low,high=upper['bounds']
                cx,cy=(low[0]+high[0])/2,(low[1]+high[1])/2
                rx,ry=(high[0]-low[0])*.35,(high[1]-low[1])*.35
                cavity(obj,(cx,cy),(rx,ry),.20,1.2)
        elif icon in ['7item095','7item096']:
            voxel_union(obj)
            # Open the underside without cutting into the soft closed crown.
            cavity(obj,(0,0),(.29,.27),-.25,.19)
        elif icon=='6hat3':
            # Straighten the cone progressively; keep brim and front hardware in place.
            for v in obj.data.vertices:
                t=max(0,min(1,(v.co.z-.4)/.5))
                v.co.x *= 1-t
                v.co.y *= 1-t
                if v.co.z>.4:v.co.z=.4+(v.co.z-.4)*1.35
            voxel_union(obj)
            cavity(obj,(0,0),(.22,.22),-.3,.35)
        else:
            raise ValueError(icon)
        voxel_union(obj,.006)
        finish(obj,name,3200 if icon.startswith('6boots') else 2800)


if __name__=='__main__':main()
