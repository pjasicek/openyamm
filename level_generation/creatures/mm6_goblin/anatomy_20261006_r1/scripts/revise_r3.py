"""Local native-likeness sculpt on the retained textured rig; no new service job."""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'anatomy_20261006_r1'
BASE=ROOT/'review_20261006/goblin_review.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene
old_positions=[v.co.copy() for v in body.data.vertices]
old_normals=[n.vector.copy() for n in body.data.corner_normals]
members={g.name:{v.index for v in body.data.vertices if any(x.group==g.index for x in v.groups)} for g in body.vertex_groups if g.name.startswith(('Component_','EarHoop'))}
core=members['Component_0'];eye_centers={}
for group in ['Component_32','Component_50']:
    eye_centers[group]=sum((old_positions[i] for i in members[group]),Vector())/len(members[group])
def smooth(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)
def gaussian(x,center,width):return math.exp(-((x-center)/width)**2)
def translation(v):
    # Retain the existing approximately upright neck joint chain; correct its puffy skin envelope.
    # The upper skull moves slightly back within that envelope, not through an animated bone translation.
    region=max(1-smooth(.13,.21,abs(v.x)),smooth(1.295,1.39,v.z))
    return .040*smooth(1.205,1.30,v.z)*region
def lift(v):return .018*smooth(1.24,1.345,v.z)*(1-smooth(1.405,1.645,v.z))
def sculpt(v):
    x,y,z=v;out=v.copy()
    if z<1.205:return out
    if z<1.39 and abs(x)<.17:
        neck=gaussian(z,1.309,.058)*(1-smooth(.085,.155,abs(x)))
        neck*=1-smooth(1.285,1.31,z)*smooth(.065,.095,-y)
        out.x=x*(1-.20*neck)
        out.y=.032+(y-.032)*(1-.27*neck)
    out.y+=translation(v)
    out.z+=lift(v)
    if y<-.075 and abs(x)<.145 and 1.290<z<1.545:
        front=smooth(.075,.130,-y)
        mouth=gaussian(z,1.386,.027)*math.exp(-(x/.100)**4)*front
        jaw=gaussian(z,1.332,.049)*front
        out.x+=x*(.30*mouth+.45*jaw)
        out.y+=.008*mouth
        if z<1.370:
            out.z+=(1.370-z)*.20*jaw
        # Define a cheekbone over a hollow, rather than retaining a full rounded cheek pad.
        hollow=gaussian(abs(x),.086,.040)*gaussian(z,1.413,.029)*front
        out.y+=.031*hollow
        out.x-=math.copysign(.009*hollow,x)
        cheekbone=gaussian(abs(x),.103,.030)*gaussian(z,1.449,.018)*front
        out.x+=math.copysign(.005*cheekbone,x)
        # Broad, short nasal plane; retain nostrils and the original UV detail.
        nose=gaussian(x,0,.041)*gaussian(z,1.435,.024)*smooth(.143,.195,-y)
        out.y+=.010*nose
        # Reduce the whole opening with its surrounding eyelids, not only the detached eyeball.
        center=eye_centers['Component_50' if x<0 else 'Component_32']
        orbit=gaussian(x,center.x,.033)*gaussian(z,center.z,.031)*front
        out.x+=(center.x-x)*.14*orbit
        out.z+=(center.z-z)*.24*orbit
        old_bulb=sum(gaussian(x,side*.057,.038)*gaussian(z,1.490,.027) for side in [-1,1])*front
        out.y+=.021*old_bulb
        ridge=gaussian(z,1.484+.19*abs(x),.017)*math.exp(-(x/.115)**4)*front
        out.y-=.026*ridge
    # Keep the native rear skull wedge and ear silhouettes; taper just the bald crown.
    if z>1.535 and abs(x)<.13 and y<.13:
        top=smooth(1.535,1.615,z)*(1-smooth(.105,.13,abs(x)))
        out.x*=1-.09*top
        out.z-=.013*smooth(.035,.105,abs(x))*top
    return out

for i in core:
    v=body.data.vertices[i];v.co=sculpt(old_positions[i])
for group,center in eye_centers.items():
    for i in members[group]:
        p=old_positions[i];v=body.data.vertices[i]
        v.co=Vector((center.x+(p.x-center.x)*.82,p.y+.002+translation(p),center.z+(p.z-center.z)*.72+lift(p)))
for group in ['Component_5','Component_23']:
    for i in members[group]:
        p=old_positions[i];v=body.data.vertices[i]
        v.co=Vector((p.x*(1+.30*gaussian(p.z,1.386,.027)+.45*gaussian(p.z,1.332,.049)),p.y+translation(p),p.z+lift(p)))
for group,indices in members.items():
    if group.startswith('EarHoop'):
        center=sum((old_positions[i] for i in indices),Vector())/len(indices)
        for i in indices:
            body.data.vertices[i].co.y+=.040
            body.data.vertices[i].co.z+=lift(center)
changed={v.index for v in body.data.vertices if (v.co-old_positions[v.index]).length>1e-8}
assert changed and all(old_positions[i].z>1.20 for i in changed)
reweighted=[]
for i in core:
    p=old_positions[i]
    if 1.299<p.z<1.390 and p.y<-.075 and abs(p.x)<.12:
        # Native lower-jaw skin must not inherit the clavicles' arm swing.
        existing={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in arm.data.bones}
        if existing.get('Head',0)+existing.get('headfront',0)+existing.get('Jaw',0)<.55:continue
        jaw_weight=.90*(1-smooth(1.369,1.388,p.z))
        for name in existing:body.vertex_groups[name].remove([i])
        body.vertex_groups['Head'].add([i],1-jaw_weight,'REPLACE')
        if jaw_weight:body.vertex_groups['Jaw'].add([i],jaw_weight,'REPLACE')
        reweighted.append(i)
body.data.update()
normal_indices=set(changed)
for face in body.data.polygons:
    if any(i in changed for i in face.vertices):normal_indices.update(face.vertices)
if body.data.has_custom_normals:
    body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
    auto=[n.vector.copy() for n in body.data.corner_normals]
    body.data.normals_split_custom_set([auto[i] if loop.vertex_index in normal_indices else old_normals[i] for i,loop in enumerate(body.data.loops)])

# Preserve the nine action curves, skeleton/bind, weights, UVs and texture maps.
arm.animation_data.action=bpy.data.actions['Standing'];arm.animation_data.action_slot=arm.animation_data.action.slots[0];scene.frame_set(1)
for o in scene.objects:o.select_set(o in [body,arm,sword])
bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'goblin_anatomy_r3.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'goblin_anatomy_r3.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_rest_position_armature=True,export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_anim_single_armature=True,export_influence_nb=4,export_all_influences=False,export_animations=True,export_yup=True,export_apply=True,export_tangents=True,export_texcoords=True,export_normals=True,export_extras=True,export_image_format='AUTO')
flips=[]
for f in body.data.polygons:
    a,b,c=f.vertices[:3];old=(old_positions[b]-old_positions[a]).cross(old_positions[c]-old_positions[a]);new=(body.data.vertices[b].co-body.data.vertices[a].co).cross(body.data.vertices[c].co-body.data.vertices[a].co)
    if old.length>1e-10 and new.length>1e-10 and old.normalized().dot(new.normalized())<0:flips.append(f.index)
report=dict(base_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),master_sha256=hashlib.sha256((OUT/'goblin_anatomy_r3.blend').read_bytes()).hexdigest(),glb_sha256=hashlib.sha256((OUT/'goblin_anatomy_r3.glb').read_bytes()).hexdigest(),changed_vertices=len(changed),reweighted_lower_jaw_vertices=len(reweighted),largest_displacement_m=max((body.data.vertices[i].co-old_positions[i]).length for i in changed),normal_recalculation='Changed head/neck and adjacent corners; original custom normals retained elsewhere.',local_normal_reversals=flips,changes=['Narrower upright neck skin envelope and clearer jaw/neck separation; upright joint chain retained.','Slight posterior skull carriage and longer exposed neck, with existing bone pivots and action curves unchanged.','Broader mouth/dentures and lower jaw, shorter chin, defined cheekbone and cheek hollow.','Smaller eyeballs and matched eyelid opening; replace globular brow bulges with a sloping orbital ridge.','Flatter short nose and more tapered bald crown; rear wedge and ears retained.','Remove demonstrated clavicle weights from the lower jaw and bind the actual jaw skin to Head/Jaw.'],unchanged=['Topology/triangles','UV coordinates and texture images','Bone hierarchy/rest matrices','All nine animation curves','All regions below the neck','Separate sword'],status='sculpted; close visual and posed-surface review pending',supersedes='First/second diagnostic sculpts exposed lip projection and a stretched chin. The actual lower chin begins near Z=1.305, below the earlier guessed mask; third pass addresses that complete shape and its clavicle weight leak. Revised from original baseline, not compounded.')
(OUT/'revision_r3.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
