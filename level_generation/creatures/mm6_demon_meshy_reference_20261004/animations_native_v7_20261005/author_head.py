"""Local head refinement on the existing topology, weights, rig and animation curves."""
import json
import math
import importlib.util
from pathlib import Path

import bpy
import bmesh
import numpy as np

STAGE = Path(__file__).resolve().parent
SOURCE = np.load(STAGE.parent/'attack_animation_v2/source_geometry.npz')
HEAD_GROUPS = {'mixamorig:Head', 'mixamorig:HeadTop_End', 'headfront', 'Bone_025'}


def smooth(value, low, high):
    t = max(0, min(1, (value-low)/(high-low)))
    return t*t*(3-2*t)


def components(mesh):
    adjacency = [set() for v in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = set()
    for i in range(len(adjacency)):
        if i in seen:
            continue
        stack, indices = [i], []
        seen.add(i)
        while stack:
            v = stack.pop()
            indices.append(v)
            for other in adjacency[v]:
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        yield indices


def apply():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    mesh = scene.objects['Demon_Native_Mesh']
    rest = SOURCE['vertices']
    # Reapplying the sculpt first removes only the pupil caps authored below.
    if len(mesh.data.vertices) > len(rest):
        bm = bmesh.new()
        bm.from_mesh(mesh.data)
        bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index >= len(rest)], context='VERTS')
        bm.to_mesh(mesh.data)
        bm.free()
    assert len(mesh.data.vertices) == len(rest)
    groups = {g.index:g.name for g in mesh.vertex_groups}
    head_weight = np.array([sum(g.weight for g in v.groups if groups[g.group] in HEAD_GROUPS)
                            for v in mesh.data.vertices])
    result = rest.copy()
    eye_components = []
    for indices in components(mesh.data):
        p = rest[indices]
        lo, hi = p.min(0), p.max(0)
        if 45 < len(indices) < 80 and lo[2] > 1.575 and hi[2] < 1.615 and hi[1] < -.33:
            eye_components.append(indices)
    assert len(eye_components) == 2
    eye_vertices = {i for component in eye_components for i in component}
    center_x = -.006
    for i, p in enumerate(rest):
        weight = float(head_weight[i])
        if weight <= .05 or i in eye_vertices:
            continue
        x, y, z = map(float, p)
        dx, side = x-center_x, -1 if x < center_x else 1
        q = p.copy()
        # Broader cranium and muzzle; taper the edit at the head/neck attachment.
        face = smooth(z, 1.48, 1.56)*(1-smooth(abs(dx), .075, .12))
        q[0] += dx*.14*face
        muzzle = math.exp(-((dx/.045)**2+((z-1.563)/.034)**2))*smooth(-y, .32, .38)
        q[0] += dx*.18*muzzle
        q[1] += .010*muzzle
        # Squarer lower jaw, with the existing hinge and teeth kept in place.
        jaw = smooth(-y, .27, .34)*(1-smooth(z, 1.53, 1.555))
        q[0] += dx*.18*jaw
        q[2] += .007*jaw
        # Reduce the central crest and soften the sharply sloping inner brow.
        crest = math.exp(-(dx/.033)**2)*smooth(z, 1.64, 1.70)
        q[2] -= .013*crest
        inner_brow = math.exp(-(dx/.026)**2-((z-1.614)/.024)**2)*smooth(-y, .30, .35)
        q[2] += .008*inner_brow
        q[1] += .008*inner_brow
        # Round the pointed rear crest into the back of the cranium.
        back = smooth(y, -.225, -.175)*smooth(z, 1.60, 1.645)*(1-smooth(abs(dx), .06, .11))
        back_limit = -.260+.102*math.sqrt(max(0, 1-((z-1.605)/.088)**2-(dx/.12)**2*.25))
        q[1] = q[1]*(1-back)+min(q[1], back_limit)*back
        for eye_x in (-.044, .029):
            ex, ez = x-eye_x, z-1.596
            influence = math.exp(-((ex/.033)**4+(ez/.030)**4))*smooth(-y, .30, .35)
            q[0] += ex*.48*influence
            q[2] += (ez*.40+.006)*influence
            q[1] += .004*influence
        # Turn the wide conical crown horns into thinner, more upright pointed ear blades.
        ear = smooth(abs(dx), .055, .105)*smooth(z, 1.605, 1.645)
        u = abs(dx)-.064
        v = z-1.630
        axis = np.array([.084, .070])
        t = (u*axis[0]+v*axis[1])/float(axis@axis)
        radial = (u*axis[1]-v*axis[0])/float(np.linalg.norm(axis))
        target_x = .074+.050*t+radial*1.15
        target_z = 1.610+.099*t-radial*.70
        q[0] = q[0]*(1-ear)+(center_x+side*target_x)*ear
        q[2] = q[2]*(1-ear)+target_z*ear
        q[1] = q[1]*(1-ear)+(-.228+(y+.228)*.40)*ear
        # Bring the existing low ear folds upward toward the larger pinnae.
        fold = math.exp(-((abs(dx)-.088)/.027)**4-((z-1.56)/.032)**4)
        fold *= 1-smooth(-y, .30, .35)
        q[2] += (.014+.025*smooth(z, 1.54, 1.58))*fold
        q[1] += .018*fold
        result[i] = p+(q-p)*min(1, weight)
    for indices in eye_components:
        p = rest[indices]
        lo, hi = p.min(0), p.max(0)
        center = (lo+hi)/2
        new_center = np.array([center[0]+(-.003 if center[0]<0 else .003), -.361, 1.602])
        radii = np.array([.0175, .0165, .0185])
        result[indices] = new_center+(p-center)/(hi-lo)*2*radii
    for vertex, point in zip(mesh.data.vertices, result):
        vertex.co = point
    # Reuse the existing material helper; these are the original detached eyeballs, not added mesh.
    spec = importlib.util.spec_from_file_location('effects', STAGE/'effects.py')
    effects = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(effects)
    materials = [('Demon_Native_Eye_Iris', (.76, .43, .39)), ('Demon_Native_Eye_Pupil', (.035, .022, .019))]
    slots = []
    for name, rgb in materials:
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = effects.material(name, rgb)
        if mat.name not in mesh.data.materials:
            mesh.data.materials.append(mat)
        slots.append(list(mesh.data.materials).index(mat))
    for polygon in mesh.data.polygons:
        if not all(i in eye_vertices for i in polygon.vertices):
            continue
        polygon.material_index = slots[0]
    # Thin elliptical surface caps give smooth pupil outlines without painting jagged face patches.
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    deform = bm.verts.layers.deform.verify()
    head_group = mesh.vertex_groups['mixamorig:Head'].index
    for indices in eye_components:
        eye = result[indices]
        center = (eye.min(0)+eye.max(0))/2
        def point(x, z):
            y = center[1]-.0165*math.sqrt(max(0, 1-((x-center[0])/.0175)**2-((z-center[2])/.0185)**2))-.0008
            vertex = bm.verts.new((x, y, z))
            vertex[deform][head_group] = 1
            return vertex
        middle = point(center[0], center[2])
        rim = [point(center[0]+.0075*math.cos(i*math.tau/24),
                     center[2]+.0100*math.sin(i*math.tau/24)) for i in range(24)]
        for i in range(24):
            face = bm.faces.new((middle, rim[i], rim[(i+1)%24]))
            face.material_index = slots[1]
            face.smooth = True
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()
    changed = np.any(result != rest, axis=1)
    assert not changed[head_weight <= .05].any()
    np.savez_compressed(STAGE/'head_shape.npz', vertices=result, modified=changed, eye_vertices=np.array(sorted(eye_vertices)))
    group_names = [g.name for g in mesh.vertex_groups]
    weights = np.zeros((len(mesh.data.vertices), len(group_names)), dtype=np.float32)
    for vertex in mesh.data.vertices:
        for g in vertex.groups:
            weights[vertex.index, g.group] = g.weight
    np.savez_compressed(STAGE/'source_geometry.npz', vertices=np.array([v.co for v in mesh.data.vertices]),
                        faces=np.array([tuple(p.vertices) for p in mesh.data.polygons]), weights=weights,
                        group_names=np.array(group_names))
    report = dict(modified_original_vertices=int(changed.sum()), added_pupil_vertices=50, added_pupil_triangles=48,
                  maximum_vertex_displacement=float(np.linalg.norm(result-rest, axis=1).max()),
                  original_connectivity_weights_bind_and_animation_curves_unchanged=True,
                  eye_vertices=sorted(eye_vertices), geometry_outside_head_support_unchanged=True)
    (STAGE/'head_geometry_changes.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='eye_vertices'}, indent=2))
    return report
