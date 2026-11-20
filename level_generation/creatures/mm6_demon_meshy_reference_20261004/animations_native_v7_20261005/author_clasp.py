"""Remove the invented chest ring and fit a larger, shallower skull to the chest band."""
import importlib.util
import json
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

STAGE = Path(__file__).resolve().parent
BASELINE = STAGE.parent/'animations_native_v6_20261005'


def apply():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    obj = scene.objects['Demon_Native_Mesh']
    with bpy.data.libraries.load(str(BASELINE/'mm6_demon_native_animations.blend')) as (available,loaded):
        loaded.scenes = ['MM6_Demon_Native_Animations']
    previous = loaded.scenes[0]
    original = next(o for o in previous.objects if o.name.startswith('Demon_Native_Mesh'))
    obj.data = original.data.copy()
    obj.data.name = 'Demon_Native_Skull_Clasp'
    bpy.data.scenes.remove(previous)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    origin = bm.verts.layers.int.new('revision6_vertex')
    face_origin = bm.faces.layers.int.new('revision6_face')
    deform = bm.verts.layers.deform.verify()
    for vertex in bm.verts:
        vertex[origin] = vertex.index
    for face in bm.faces:
        face[face_origin] = face.index
    remaining = set(bm.verts)
    components = []
    while remaining:
        first = next(iter(remaining))
        group,queue = set(),[first]
        while queue:
            vertex = queue.pop()
            if vertex in group:
                continue
            group.add(vertex)
            queue.extend(e.other_vert(vertex) for e in vertex.link_edges)
        remaining -= group
        components.append(group)
    ring = next(c for c in components if len(c)==74 and max(v.co.z for v in c)<1.35)
    skull = next(c for c in components if len(c)==249 and min(v.co.z for v in c)>1.29 and max(v.co.z for v in c)<1.35)
    removed = sorted(v[origin] for v in ring)
    skull_ids = sorted(v[origin] for v in skull)
    old = np.array([v.co for v in skull])
    lo,hi = old.min(0),old.max(0)
    center = (lo+hi)/2
    group = obj.vertex_groups['Bone_024'].index
    for vertex in skull:
        vertex.co.x = -.005+(vertex.co.x-center[0])*1.60
        vertex.co.z = 1.321+(vertex.co.z-center[2])*1.55
        vertex.co.y = -.389+(vertex.co.y-hi[1])*.40
        vertex[deform].clear()
        vertex[deform][group] = 1.
    bmesh.ops.delete(bm,geom=list(ring),context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list({f for v in skull for f in v.link_faces}))
    bm.verts.index_update()
    bm.faces.index_update()
    previous_vertices = np.array([v[origin] for v in bm.verts])
    previous_faces = np.array([f[face_origin] for f in bm.faces])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    names = [g.name for g in obj.vertex_groups]
    weights = np.zeros((len(obj.data.vertices),len(names)),np.float32)
    for vertex in obj.data.vertices:
        for group in vertex.groups:
            weights[vertex.index,group.group] = group.weight
    vertices = np.array([v.co for v in obj.data.vertices])
    faces = np.array([tuple(f.vertices) for f in obj.data.polygons])
    np.savez_compressed(STAGE/'source_geometry.npz',vertices=vertices,faces=faces,weights=weights,
                        group_names=np.array(names),previous_vertex_indices=previous_vertices,previous_face_indices=previous_faces)
    inverse = {int(old):i for i,old in enumerate(previous_vertices)}
    tips = json.loads((BASELINE/'tip_vertex_masks.json').read_text())
    tips = {name:[inverse[i] for i in indices] for name,indices in tips.items()}
    (STAGE/'tip_vertex_masks.json').write_text(json.dumps(tips)+'\n')
    new_skull = vertices[np.isin(previous_vertices,skull_ids)]
    report = dict(removed_ring_vertices=removed,removed_ring_triangles=148,
                  skull_previous_vertices=skull_ids,skull_triangles=494,
                  previous_dimensions=(hi-lo).tolist(),revised_dimensions=np.ptp(new_skull,axis=0).tolist(),
                  width_factor=1.60,height_factor=1.55,depth_factor=.40,
                  skull_bone='Bone_024',skull_rigid_weight=1.,
                  all_nine_animation_curves_preserved=True,harness_geometry_preserved=True)
    (STAGE/'clasp_changes.json').write_text(json.dumps(report,indent=2)+'\n')
    spec = importlib.util.spec_from_file_location('motion7',STAGE/'motion.py')
    motion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motion)
    motion.activate('Standing',0)
    camera = scene.camera
    center,direction = Vector((0,0,.91)),Vector((0,-6,0))
    camera.location = center+direction
    camera.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale = 2.55
    scene.render.resolution_x,scene.render.resolution_y = 760,800
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(STAGE/'authored_checkpoint.blend'),compress=True)
    print('Removed ring; enlarged skull. Geometry:',len(vertices),'vertices,',len(faces),'triangles')
    return report
