"""Half-frame weapon/head intersections and equipment floor clearance, including the twin barrel configuration."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parents[1]
source, tag, *clips = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
groups = [g.name for g in body.vertex_groups]
head_bones = {'B_Head', 'Bone_025', 'headfront', 'Bone_041', 'Bone_036'}
head = [sum(e.weight for e in v.groups if groups[e.group] in head_bones) > .5 for v in body.data.vertices]
faces = [tuple(p.vertices) for p in body.data.polygons if all(head[i] for i in p.vertices)]
objects = [o for o in bpy.data.objects if o.name == 'Thunder_Maul' or o.name.startswith('Apron_')] if tag.startswith('forge') else [
    bpy.data.objects[n] for n in ('Rifle', 'TwinLance', 'Ancient_Graft')]

def evaluated(obj):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    polygons = [tuple(p.vertices) for p in mesh.polygons]
    ev.to_mesh_clear()
    return vertices, polygons

report = {}
for clip in clips:
    action = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    entries = {o.name: {'head_intersection_frames': [], 'floor_min_m': 1e9} for o in objects}
    for f in np.arange(action.frame_range[0], action.frame_range[1]+.001, .5):
        bpy.context.scene.frame_set(int(f), subframe=float(f-int(f)))
        points, _ = evaluated(body)
        head_tree = BVHTree.FromPolygons(points, faces)
        for obj in objects:
            points, polygons = evaluated(obj)
            tree = BVHTree.FromPolygons(points, polygons)
            entry = entries[obj.name]
            if head_tree.overlap(tree):
                entry['head_intersection_frames'].append(float(f))
            entry['floor_min_m'] = min(entry['floor_min_m'], min(p.z for p in points))
    report[clip] = entries
    print('EQUIPMENT', clip, {n: {'head_frames': len(e['head_intersection_frames']),
          'floor_cm': round(e['floor_min_m']*100, 2)} for n, e in entries.items()}, flush=True)
(P / f'review/equipment_{tag}.json').write_text(json.dumps(report, indent=2)+'\n')
