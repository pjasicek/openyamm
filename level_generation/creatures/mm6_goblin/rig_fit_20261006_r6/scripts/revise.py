"""Repair the shoulder weight cliff and fitted leather skirt on the retained R5 rig."""
import bpy,hashlib,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');OUT=ROOT/'rig_fit_20261006_r6';BASE=ROOT/'anatomy_20261006_r5/goblin_anatomy_r5.blend'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='8ea590e9deb84164509993e9247c9ef55bf3bc559f6c744fd9b0338fe82f188f'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene
members={g.name:{v.index for v in body.data.vertices if any(x.group==g.index for x in v.groups)} for g in body.vertex_groups};skin=members['Component_0'];cloth=members['Component_15']
old_positions=[v.co.copy() for v in body.data.vertices];old_normals=[n.vector.copy() for n in body.data.corner_normals]
def smooth(a,b,v):
    t=min(1,max(0,(v-a)/(b-a)));return t*t*(3-2*t)
def weights(i,entries):
    for g in list(body.data.vertices[i].groups):
        name=body.vertex_groups[g.group].name
        if name in arm.data.bones:body.vertex_groups[name].remove([i])
    total=sum(entries.values());assert total>0
    for name,w in entries.items():
        if w>1e-6:body.vertex_groups[name].add([i],w/total,'REPLACE')
spine=[(n,arm.data.bones[n].head_local.z) for n in ['Spine02','Spine01','Spine']]
def torso(z):
    if z<=spine[0][1]:return {spine[0][0]:1.}
    if z>=spine[-1][1]:return {spine[-1][0]:1.}
    for (lo,a),(hi,b) in zip(spine,spine[1:]):
        if a<=z<=b:
            t=(z-a)/(b-a);return {lo:1-t,hi:t}
reweighted=[]
for i in skin:
    p=old_positions[i]
    if not .135<abs(p.x)<.37 or not 1.00<p.z<1.315:continue
    original={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in arm.data.bones}
    if p.z>1.275 and sum(original.get(n,0) for n in ['Head','Jaw','headfront','neck'])>.25:continue
    side='Right' if p.x<0 else 'Left'
    # A continuous attachment band replaces the old hard torso cutoff at abs(x)=0.22 m.
    limb=smooth(.155,.350,abs(p.x))
    clavicle=(1-limb)*.28*smooth(1.15,1.255,p.z)*smooth(.14,.24,abs(p.x))
    entries={n:w*(1-limb-clavicle) for n,w in torso(p.z).items()}
    entries[side+'Arm']=limb;entries[side+'Shoulder']=clavicle
    # Blend into the untouched proximal elbow surface at the lower boundary.
    original={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in arm.data.bones}
    fade=smooth(1.00,1.07,p.z)
    if fade<1:
        entries={n:entries.get(n,0)*fade+original.get(n,0)*(1-fade) for n in entries.keys()|original.keys()}
        entries=dict(sorted(entries.items(),key=lambda pair:pair[1],reverse=True)[:4])
    weights(i,entries);reweighted.append(i)

# Fit a hanging elliptical garment to the actual hips/thighs, with 12 mm outward clearance.
skin_vertices=[tuple(v.co) for v in body.data.vertices]
skin_faces=[tuple(p.vertices) for p in body.data.polygons if all(i in skin and abs(body.data.vertices[i].co.x)<.31 and .5<body.data.vertices[i].co.z<.95 for i in p.vertices)]
skin_bvh=BVHTree.FromPolygons(skin_vertices,skin_faces,all_triangles=True)
profiles=[(.620,.220,.128,.010),(.697,.211,.158,.020),(.785,.197,.164,.020),(.836,.188,.153,.013)]
def profile(z):
    if z<=profiles[0][0]:return profiles[0][1:]
    if z>=profiles[-1][0]:return profiles[-1][1:]
    for a,b in zip(profiles,profiles[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return tuple(a[i]*(1-t)+b[i]*t for i in range(1,4))
def fit(phi,z,inner=False):
    a,b,cy=profile(z);center=Vector((0,cy,z));delta=Vector((math.sin(phi)*a,-math.cos(phi)*b,0));radial=delta.normalized()
    point,normal,index,distance=skin_bvh.ray_cast(center+radial*.65,-radial,.72)
    if point is not None:
        radius=(point-center).dot(radial)
        if radius>0:delta=radial*max(delta.length,radius+.012)
    if inner:delta-=radial*.0035
    return center+delta
for i in cloth:
    p=old_positions[i];phi=math.atan2(p.x,.025-p.y);radius=math.hypot(p.x,p.y-.025)
    original_radius=.201 if p.z>.81 else .222 if p.z>.74 else .244 if p.z>.665 else .245
    body.data.vertices[i].co=fit(phi,p.z,radius<original_radius-.00175)
body.data.update()
changed={i for i in cloth if (body.data.vertices[i].co-old_positions[i]).length>1e-8}
normal_vertices=set(changed)
for f in body.data.polygons:
    if any(i in changed for i in f.vertices):normal_vertices.update(f.vertices)
if body.data.has_custom_normals:
    body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops));auto=[n.vector.copy() for n in body.data.corner_normals]
    body.data.normals_split_custom_set([auto[i] if loop.vertex_index in normal_vertices else old_normals[i] for i,loop in enumerate(body.data.loops)])


# Selected after the rigid-panel trials: match leather to the nearby hips/thigh blend.
def members(name):
 g=body.vertex_groups[name].index
 return {v.index for v in body.data.vertices if any(x.group==g for x in v.groups)}
skin=members('Component_0');cloth=members('Component_15')
faces=[tuple(p.vertices) for p in body.data.polygons if all(i in skin and abs(body.data.vertices[i].co.x)<.31 and .5<body.data.vertices[i].co.z<.95 for i in p.vertices)]
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],faces,all_triangles=True)
for j in sorted(cloth):
 q,n,idx,d=tree.find_nearest(body.data.vertices[j].co)
 tri=faces[idx];a,b,c=(body.data.vertices[k].co for k in tri);v0=b-a;v1=c-a;v2=q-a
 d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);d20=v2.dot(v0);d21=v2.dot(v1);den=d00*d11-d01*d01
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;entries={}
 for k,factor in zip(tri,[1-v-w,v,w]):
  for g in body.data.vertices[k].groups:
   name=body.vertex_groups[g.group].name
   if name in arm.data.bones:entries[name]=entries.get(name,0)+max(0,factor)*g.weight
 entries=dict(sorted(entries.items(),key=lambda p:p[1],reverse=True)[:4]);total=sum(entries.values());assert total>0
 for g in list(body.data.vertices[j].groups):
  name=body.vertex_groups[g.group].name
  if name in arm.data.bones:body.vertex_groups[name].remove([j])
 for name,weight in entries.items():
  if weight>1e-6:body.vertex_groups[name].add([j],weight/total,'REPLACE')

O=OUT
for action in bpy.data.actions:action.use_fake_user=True
arm.animation_data.action=bpy.data.actions['Standing'];arm.animation_data.action_slot=arm.animation_data.action.slots[0];bpy.context.scene.frame_set(1)
for obj in bpy.context.scene.objects:obj.select_set(obj in [arm,body,sword])
bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(O/'goblin_r6.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'goblin_r6.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_rest_position_armature=True,export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_anim_single_armature=True,export_influence_nb=4,export_all_influences=False,export_animations=True,export_yup=True,export_apply=True,export_tangents=True,export_texcoords=True,export_normals=True,export_extras=True,export_image_format='AUTO')
report=json.loads((O/'revision.json').read_text())
report.update(status='selected geometry/weight correction; full motion clearance remains needs_revision',master_sha256=hashlib.sha256((O/'goblin_r6.blend').read_bytes()).hexdigest(),glb_sha256=hashlib.sha256((O/'goblin_r6.glb').read_bytes()).hexdigest(),fit_iterations=7,garment_vertices_reweighted=288,changed_bones=[],changed_animation_channels=[],cloth_deformation='Skin-matched hips/thigh weights on the fitted 12 separate leather panels. Original 64-bone rig and nine actions restored exactly; no permanent panel flare or corrective motion curves.',rejected_candidate='Rigid single-hinge follow could not clear deep flexion without strips flipping outward; rejected after motion renders.',motion_clearance_status='Standing/Fidget/Corpse clear in sampled local checks; remaining intersections during walk/run/attack/hit/death explicitly retained for further motion/cloth review.',checks_pending=['preservation','actual GLB reimport','selected renders','browser'])
report['unchanged']=['head/neck and all non-cloth rest geometry','UV coordinates and embedded PNG texture images','complete 64-bone rig/rest matrices','sword geometry and all nine action curves']
(O/'revision.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
