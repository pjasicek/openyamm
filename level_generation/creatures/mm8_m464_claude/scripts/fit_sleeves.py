"""Refit the jacket sleeves to the accepted F3 arm cross-sections and skin weights."""
import bpy
import json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def fit_sleeves(body, rig, project):
    before_objects = set(bpy.data.objects)
    with bpy.data.libraries.load(str(project / 'work/source_body.blend'), link=False) as (src, dst):
        dst.objects = ['Body']
    source = dst.objects[0]
    source.data.calc_loop_triangles()
    source_co = np.array([v.co[:] for v in source.data.vertices])
    source_names = [g.name for g in source.vertex_groups]
    source_w = np.zeros((len(source_co), len(source_names)))
    for vertex in source.data.vertices:
        for group in vertex.groups:
            source_w[vertex.index, group.group] = group.weight
    co = np.array([v.co[:] for v in body.data.vertices])
    original = co.copy()
    parts = np.array([v.value for v in body.data.attributes['part'].data])
    names = [g.name for g in body.vertex_groups]
    weights = np.zeros((len(co), len(names)))
    for vertex in body.data.vertices:
        for group in vertex.groups:
            weights[vertex.index, group.group] = group.weight
    report = {}
    changed = np.zeros(len(co), dtype=bool)

    def profile(points, mask, shoulder, axis, basis, samples):
        longitudinal = (points - shoulder) @ axis
        transverse = (points - shoulder) @ basis.T
        rows = []
        for t in samples:
            near = mask & (abs(longitudinal - t) < .045)
            xy = transverse[near]
            kernel = np.exp(-.5 * ((longitudinal[near] - t) / .018) ** 2)
            assert len(xy) >= 5, (t, len(xy))
            matrix = np.c_[2 * xy, np.ones(len(xy))]
            fit = np.linalg.lstsq(matrix * kernel[:, None] ** .5,
                                 (xy * xy).sum(1) * kernel ** .5, rcond=None)[0]
            rows.append([*fit[:2], np.sqrt(max(0, fit[2] + sum(fit[:2] ** 2)))])
        return np.array(rows)

    for side in 'LR':
        shoulder, elbow, wrist = [np.array(rig.data.bones[f'B_{side}_{n}'].head_local)
                                  for n in ['UpperArm', 'Forearm', 'Hand']]
        axis = wrist - shoulder
        length = np.linalg.norm(axis)
        axis /= length
        y = np.array([0., 1., 0.])
        y -= y.dot(axis) * axis
        y /= np.linalg.norm(y)
        basis = np.array([y, np.cross(axis, y)])
        columns = [i for i, name in enumerate(names) if name.startswith(f'B_{side}_')
                   and any(k in name for k in ['UpperArm', 'Forearm', 'Hand'])]
        source_columns = [i for i, name in enumerate(source_names) if name.startswith(f'B_{side}_')
                          and any(k in name for k in ['UpperArm', 'Forearm', 'Hand'])]
        sleeve = (parts == 2) & (weights[:, columns].sum(1) > .7)
        skin = source_w[:, source_columns].sum(1) > .7
        samples = np.linspace(.045, length - .005, 45)
        old = profile(co, sleeve, shoulder, axis, basis, samples)
        target = profile(source_co, skin, shoulder, axis, basis, samples)
        faces = [t.vertices[:] for t in source.data.loop_triangles if skin[list(t.vertices)].all()]
        tree = BVHTree.FromPolygons([Vector(x) for x in source_co], faces, all_triangles=True)
        longitudinal = (co - shoulder) @ axis
        arm_share = weights[:, columns].sum(1)
        ids = np.flatnonzero((parts == 2) & (arm_share > .05) & (longitudinal > -.025))
        for i in ids:
            t = longitudinal[i]
            current = np.array([np.interp(t, samples, old[:, j]) for j in range(3)])
            desired = np.array([np.interp(t, samples, target[:, j]) for j in range(3)])
            xy = (co[i] - shoulder) @ basis.T
            # Fade through the entire shoulder attachment, avoiding a hard moved/unmoved seam.
            blend = np.clip((t + .025) / .085, 0, 1)
            blend = blend * blend * (3 - 2 * blend)
            share = np.clip((arm_share[i] - .05) / .70, 0, 1)
            blend *= share * share * (3 - 2 * share)
            radius_scale = (desired[2] + .002) / current[2]
            # The source has a loose short blouse sleeve; keep this jacket's slimmer upper-arm girth.
            radius_scale = min(radius_scale, 1.08 + .3 * np.clip((t - .15) / .08, 0, 1))
            fitted = desired[:2] + (xy - current[:2]) * radius_scale
            co[i] += (fitted - xy) @ basis * blend
            q, normal, triangle, distance = tree.find_nearest(Vector(co[i]))
            tri = list(faces[triangle])
            a, b, c = source_co[tri]
            uv = np.linalg.lstsq(np.array([b - a, c - a]).T, np.array(q) - a, rcond=None)[0]
            bary = np.maximum([1 - uv.sum(), uv[0], uv[1]], 0)
            bary /= bary.sum()
            transferred = bary @ source_w[tri]
            row = np.array([transferred[source_names.index(name)] if name in source_names else 0
                            for name in names])
            weight_blend = np.clip((t - .08) / .08, 0, 1)
            weight_blend = blend * weight_blend * weight_blend * (3 - 2 * weight_blend)
            row = weights[i] * (1 - weight_blend) + row * weight_blend
            keep = np.argsort(row)[-4:]
            row[np.setdiff1d(np.arange(len(row)), keep)] = 0
            row /= row.sum()
            for group in body.vertex_groups:
                group.remove([int(i)])
            for j in np.flatnonzero(row > 1e-7):
                body.vertex_groups[int(j)].add([int(i)], float(row[j]), 'REPLACE')
            body.data.vertices[int(i)].co = Vector(co[i])
            changed[i] = True
        report[side] = {'vertices': len(ids), 'max_refit_mm': float(np.linalg.norm(co[ids] - original[ids], axis=1).max() * 1000),
                        'profile_samples_m': samples.tolist(), 'before_profile_m': old.tolist(),
                        'accepted_arm_profile_m': target.tolist()}
    assert np.array_equal(co[~changed], original[~changed])
    assert np.all(parts[changed] == 2)
    for obj in set(bpy.data.objects) - before_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    destination = project / 'review/arm_fix'
    destination.mkdir(exist_ok=True)
    (destination / 'sleeve_fit.json').write_text(json.dumps(report, indent=2) + '\n')
