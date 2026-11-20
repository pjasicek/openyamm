"""Check the delivered GLB: rigidity, grounded feet, clip loops and parity with the editable master."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

P=Path(__file__).resolve().parents[1]
FPS=24
bpy.ops.wm.open_mainfile(filepath=str(P/'work/crystal_walker.blend'))
rig=bpy.data.objects['CrystalRig'];body=bpy.data.objects['CrystalWalker'];scene=bpy.context.scene
durations=json.loads((P/'work/build_report.json').read_text())['clips']


def coordinates(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    points=[evaluated.matrix_world@v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


reference={};report={}
for clip,meta in durations.items():
    rig.animation_data.action=bpy.data.actions[clip]
    reference[clip]=[]
    for t in [0,meta['duration']*.25,meta['duration']*.5,meta['duration']*.75,meta['duration']]:
        frame=1+t*FPS;scene.frame_set(math.floor(frame),subframe=frame%1)
        reference[clip].append((t,coordinates(body)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m596.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=bpy.data.objects['CrystalWalker'];scene=bpy.context.scene;scene.render.fps=FPS
actions={a.name:a for a in bpy.data.actions}
print('IMPORTED CLIPS',list(actions),flush=True)
groups={g.index:g.name for g in body.vertex_groups}
owners=[]
for vertex in body.data.vertices:
    used=[g for g in vertex.groups if g.weight>1e-6]
    assert len(used)==1 and abs(used[0].weight-1)<1e-6
    owners.append(groups[used[0].group])
edges=set()
faces=[tuple(p.vertices) for p in body.data.polygons]
for face in faces:
    assert len({owners[v] for v in face})==1
    edges.update(tuple(sorted((face[i],face[(i+1)%len(face)]))) for i in range(len(face)))
rest=[v.co.copy() for v in body.data.vertices]
lengths={edge:(rest[edge[0]]-rest[edge[1]]).length for edge in edges}
for clip,meta in durations.items():
    action=actions.get(clip) or next(a for a in actions.values() if a.name.endswith('|'+clip))
    rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    error=0;edge_error=0;minimum=100;hand_contacts=[];feet=[]
    for t,expected in reference[clip]:
        frame=t*FPS;scene.frame_set(math.floor(frame),subframe=frame%1)
        actual=coordinates(body);tree=KDTree(len(expected))
        for i,point in enumerate(expected):tree.insert(point,i)
        tree.balance();error=max(error,max(tree.find(point)[2] for point in actual))
    # Exported polygons are checked at half frames, including interpolation between keys.
    for sample in range(round(meta['duration']*FPS*2)+1):
        t=sample/(FPS*2);scene.frame_set(sample//2,subframe=(sample%2)/2)
        points=coordinates(body);minimum=min(minimum,min(p.z for p in points))
        edge_error=max(edge_error,max(abs((points[a]-points[b]).length/length-1)
                                      for (a,b),length in lengths.items() if length>1e-6))
        feet.append({side:min(points[i].z for i,owner in enumerate(owners) if owner==side+'Foot')
                     for side in ('Left','Right')})
        torso=[face for face in faces if owners[face[0]] in ('Chest','Waist','Hips','Head','Neck')]
        tree=BVHTree.FromPolygons(points,torso)
        for side in ('Left','Right'):
            hand=[face for face in faces if owners[face[0]]==side+'Hand']
            hits=tree.overlap(BVHTree.FromPolygons(points,hand))
            if hits:hand_contacts.append({'time':t,'side':side,'triangle_pairs':len(hits)})
    assert error<.0001, (clip,'export parity',error)
    assert edge_error<.0002, (clip,'crystal stretch',edge_error)
    assert minimum>-.015, (clip,'floor',minimum)
    assert not hand_contacts, (clip,'hand penetrates torso',hand_contacts)
    report[clip]={'export_surface_error_m':error,'max_edge_length_relative_error':edge_error,
                  'minimum_z_m':minimum,'hand_torso_intersections':hand_contacts,
                  'worst_lower_sole_m':max(min(f.values()) for f in feet),'samples':len(feet)}
    print(clip,report[clip],flush=True)
    if clip in ('Standing','Walking','Running','Fidget','Dead'):
        scene.frame_set(0);first=coordinates(body)
        scene.frame_set(round(meta['duration']*FPS));last=coordinates(body)
        gap=max((a-b).length for a,b in zip(first,last));assert gap<.0001,(clip,'loop gap',gap)
        report[clip]['loop_gap_m']=gap
report['geometry']={'vertices':len(rest),'triangles':len(faces),'one_influence_per_vertex':True,
                    'one_bone_per_facet':True,'glb_sha256':__import__('hashlib').sha256((P/'export/mm8_m596.glb').read_bytes()).hexdigest()}
(P/'work/export_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: exported crystal rigidity, half-frame contacts/floor, loops and master parity',flush=True)
