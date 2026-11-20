"""Compare actual shoulder stretch and cloth/body clearance across the retained clips."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');OUT=ROOT/'rig_fit_20261006_r6'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'goblin_r6.blend'))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];scene=bpy.context.scene
members={g.name:{v.index for v in body.data.vertices if any(x.group==g.index for x in v.groups)} for g in body.vertex_groups};skin=members['Component_0'];cloth=members['Component_15']
region={i for i in skin if .12<abs(body.data.vertices[i].co.x)<.42 and 1.03<body.data.vertices[i].co.z<1.325}
edges=np.array([tuple(e.vertices) for e in body.data.edges if all(i in region for i in e.vertices)])
rest=np.array([tuple(v.co) for v in body.data.vertices]);lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
skin_faces=[tuple(p.vertices) for p in body.data.polygons if all(i in skin for i in p.vertices)]
lower_faces={i for i,p in enumerate(skin_faces) if all(abs(body.data.vertices[j].co.x)<.31 and .5<body.data.vertices[j].co.z<.95 for j in p)}
cloth_faces=[tuple(p.vertices) for p in body.data.polygons if all(i in cloth for i in p.vertices)]
cloth_edges=[tuple(e.vertices) for e in body.data.edges if all(i in cloth for i in e.vertices)]
reports={};samples=[]
for a in bpy.data.actions:
    arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];duration=(a.frame_range[1]-a.frame_range[0])/192;rows=[]
    for t in np.linspace(0,duration,max(13,round(duration*48)+1)):
        f=1+t*192;scene.frame_set(int(f),subframe=float(f-int(f)))
        mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;positions=[v.co.copy() for v in mesh.vertices];arr=np.array(positions)
        ratios=np.linalg.norm(arr[edges[:,0]]-arr[edges[:,1]],axis=1)/lengths
        tree=BVHTree.FromPolygons(positions,skin_faces,all_triangles=True)
        probes=[(str(i),positions[i]) for i in sorted(cloth)]
        probes += [('face:'+str(i),sum((positions[j] for j in face),Vector())/len(face)) for i,face in enumerate(cloth_faces)]
        probes += [('edge:'+str(i),(positions[u]+positions[v])*.5) for i,(u,v) in enumerate(cloth_edges)]
        distances=[]
        for label,p in probes:
            q,n,idx,d=tree.find_nearest(p)
            if q is not None and idx in lower_faces:distances.append((float((p-q).dot(n)),label,tuple(p)))
        worst=min(distances);bad=[r for r in distances if r[0]<-.003]
        row=dict(time_seconds=float(t),shoulder_maximum_edge_stretch=float(ratios.max()),shoulder_p95_edge_stretch=float(np.percentile(ratios,95)),cloth_minimum_signed_distance_m=worst[0],cloth_probes_inside_skin=len(bad),worst_cloth_probe=dict(label=worst[1],position=worst[2]),cloth_minimum_ground_z_m=float(arr[list(cloth),2].min()))
        rows.append(row)
    reports[a.name]=dict(samples=len(rows),maximum_shoulder_edge_stretch=max(r['shoulder_maximum_edge_stretch'] for r in rows),minimum_cloth_signed_distance_m=min(r['cloth_minimum_signed_distance_m'] for r in rows),maximum_cloth_probes_inside_skin=max(r['cloth_probes_inside_skin'] for r in rows),minimum_cloth_ground_z_m=min(r['cloth_minimum_ground_z_m'] for r in rows),worst_cloth_pose=min(rows,key=lambda r:r['cloth_minimum_signed_distance_m']),rows=rows)
    print(a.name,json.dumps({k:v for k,v in reports[a.name].items() if k!='rows'}),flush=True)
(OUT/'review/surface_checks.json').write_text(json.dumps(dict(status='measured; evaluate findings before selection',scope='evaluated shoulders and skirt vertices/edges/triangle centroids against connected skin BVH; signed nearest distance is a local diagnostic, not complete collision certification',clips=reports),indent=2)+'\n')
