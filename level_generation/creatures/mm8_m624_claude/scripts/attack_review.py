"""Check the six swept blades against each other and the complete skinned body at 96 Hz."""
import bpy,json,itertools,math
from mathutils import Vector
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m624.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=bpy.data.actions['Attack']
D=json.loads((P/'work/rig.json').read_text());wrists={}
weapons=[o for o in bpy.data.objects if o.name.endswith('_Weapon')];faces={};full_weapon_faces={};hits={}
for ob in [body]+weapons:
    ob.data.calc_loop_triangles()
    faces[ob.name]=[list(t.vertices) for t in ob.data.loop_triangles]
    if ob in weapons:
        full_weapon_faces[ob.name]=faces[ob.name][:]
        inverse=rig.data.bones[ob.name[:2]+'_Sword'].matrix_local.inverted()
        faces[ob.name]=[f for f in faces[ob.name] if all((inverse@ob.data.vertices[v].co).y>.1 for v in f)]
arm_faces={};previous={};rotation_steps={};endpoints={}
for sd in D["hands"]:
    owned={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith(sd+"_"))>.6}
    arm_faces[sd]=[f for f in faces["Body"] if all(v in owned for v in f)]
for quarter_frame in range(169):
    frame=quarter_frame/4;bpy.context.scene.frame_set(int(frame),subframe=frame%1)
    for sd in D['hands']:
        q=rig.pose.bones[sd+'_Hand'].matrix.to_quaternion()
        if sd in previous:
            angle=math.degrees(q.rotation_difference(previous[sd]).angle);angle=min(angle,360-angle)
            if angle>rotation_steps.get(sd,{}).get('degrees',0):rotation_steps[sd]={'frame':frame,'degrees':angle}
        previous[sd]=q.copy()
    deps=bpy.context.evaluated_depsgraph_get();trees={}
    for ob in [body]+weapons:
        ev=ob.evaluated_get(deps);trees[ob.name]=BVHTree.FromPolygons([ev.matrix_world@v.co for v in ev.data.vertices],faces[ob.name],all_triangles=True)
    for sd,hand in D['hands'].items():
        pb=rig.pose.bones[sd+'_Hand'];delta=pb.matrix.to_3x3()@rig.data.bones[pb.name].matrix_local.to_3x3().inverted();fwd=delta@Vector(hand['forward']);fore=rig.pose.bones[sd+'_Forearm'];angle=math.degrees(fwd.angle(fore.tail-fore.head));wrists[sd]=max(wrists.get(sd,0),angle)
    ev=body.evaluated_get(deps);positions=[ev.matrix_world@v.co for v in ev.data.vertices]
    if quarter_frame in (0,168):endpoints[quarter_frame]=positions
    arms={sd:BVHTree.FromPolygons(positions,f,all_triangles=True) for sd,f in arm_faces.items()}
    for a,b in itertools.combinations(arms,2):
        overlap=arms[a].overlap(arms[b])
        if overlap:
            va={v for fa,fb in overlap for v in arm_faces[a][fa]};vb={v for fa,fb in overlap for v in arm_faces[b][fb]}
            detail={'frame':frame,'triangle_pairs':len(overlap),'bones_a':sorted({body.vertex_groups[g.group].name for v in va for g in body.data.vertices[v].groups if g.weight>.3}),'bones_b':sorted({body.vertex_groups[g.group].name for v in vb for g in body.data.vertices[v].groups if g.weight>.3}),'center':list(sum((positions[v] for v in va|vb),Vector())/len(va|vb))}
            detail['rest_shoulder_distances_m']={sd:[min((body.data.vertices[v].co-Vector(D['joints'][sd+'_UpperArm'])).length for v in ids),max((body.data.vertices[v].co-Vector(D['joints'][sd+'_UpperArm'])).length for v in ids)] for sd,ids in [(a,va),(b,vb)]}
            hits.setdefault(a+' arm / '+b+' arm',[]).append(detail)
    full_weapons={}
    for ob in weapons:
        ev=ob.evaluated_get(deps);full_weapons[ob.name]=BVHTree.FromPolygons([ev.matrix_world@v.co for v in ev.data.vertices],full_weapon_faces[ob.name],all_triangles=True)
    for a,b in itertools.combinations(full_weapons,2):
        overlap=full_weapons[a].overlap(full_weapons[b])
        if overlap:hits.setdefault(a+' complete / '+b+' complete',[]).append({'frame':frame,'triangle_pairs':len(overlap)})
    for weapon,tree in full_weapons.items():
        for sd,arm in arms.items():
            if weapon.startswith(sd):continue
            overlap=tree.overlap(arm)
            if overlap:
                ids={v for fw,fa in overlap for v in arm_faces[sd][fa]};detail={'frame':frame,'triangle_pairs':len(overlap),'bones':sorted({body.vertex_groups[g.group].name for v in ids for g in body.data.vertices[v].groups if g.weight>.3})}
                hits.setdefault(weapon+' complete / '+sd+' arm',[]).append(detail)
    for a,b in itertools.combinations(trees,2):
        overlap=trees[a].overlap(trees[b])
        if overlap:
            detail={'frame':frame,'triangle_pairs':len(overlap)}
            if a=='Body':
                ids={v for fa,fb in overlap for v in faces['Body'][fa]};detail['body_bones']=sorted({body.vertex_groups[g.group].name for i in ids for g in body.data.vertices[i].groups if g.weight>.3})
            hits.setdefault(a+' / '+b,[]).append(detail)
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());standing=[ev.matrix_world@v.co for v in ev.data.vertices]
endpoint_error=max((a-b).length for p in endpoints.values() for a,b in zip(p,standing))
# Retain existing contact at the attached shoulder caps separately from free arm/weapon collisions.
junctions={};moving_hits={}
for pair,contacts in hits.items():
    inherited=any(c['frame']==0 for c in contacts)
    for c in contacts:
        root=inherited and ' arm / ' in pair and all(n.endswith('_UpperArm') for key in ['bones_a','bones_b'] for n in c[key]) and max(v[1] for v in c['rest_shoulder_distances_m'].values())<.16
        (junctions if root else moving_hits).setdefault(pair,[]).append(c)
report={'moving_part_intersections':moving_hits,'inherited_shoulder_junction_contacts':junctions,'shoulder_junction_rule':'Only pairs already touching in the original resting pose, entirely upper-arm skin within 0.16 m of each shoulder; all raw contacts retained.','rest_pose_endpoint_error_m':endpoint_error,'samples':169,'fps':96,'surface_intersections':hits,'maximum_wrist_swing_deg':wrists,'maximum_hand_rotation_step_96fps':rotation_steps};(P/'review/attack_r3/swept_blades.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert not moving_hits,'Moving arm/weapon surface intersection'
assert max(wrists.values())<60,'Wrist swing exceeds 60 degrees'

assert max(v['degrees'] for v in rotation_steps.values())<25,'Abrupt hand rotation between poses'

assert endpoint_error<.0001,'Attack must start and finish in the resting pose'
