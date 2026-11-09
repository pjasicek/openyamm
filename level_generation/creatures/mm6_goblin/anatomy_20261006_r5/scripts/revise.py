"""User-guided brow and jaw correction on R4. Preserve existing rig and motion."""
import bpy,hashlib,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'anatomy_20261006_r5';BASE=ROOT/'anatomy_20261006_r1/goblin_anatomy_r4.blend'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='be2172aabcf7ece357e6aac667211464ecba0a1fb5ceaa426035d67e7d18bc62'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
body=bpy.data.objects['Goblin_Body'];arm=bpy.data.objects['Goblin_Rig'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene
old=[v.co.copy() for v in body.data.vertices];normals=[n.vector.copy() for n in body.data.corner_normals]
core=body.vertex_groups['Component_0'].index
def smooth(a,b,v):
    t=min(1,max(0,(v-a)/(b-a)));return t*t*(3-2*t)
def g(v,c,w):return math.exp(-((v-c)/w)**2)
for v in body.data.vertices:
    if not any(x.group==core for x in v.groups):continue
    x,y,z=old[v.index]
    if y>=-.04 or abs(x)>.15 or not 1.30<z<1.56:continue
    front=smooth(.040,.085,-y)
    # The old brow ends in a wedge. Recede its upper projection while retaining the eyelid rim.
    brow=g(z,1.504,.027)*math.exp(-(x/.115)**4)*smooth(1.479,1.496,z)*front
    v.co.y+=.024*brow
    # Separate compact supraorbital pads from the central glabella instead of a continuous shelf.
    pads=g(abs(x),.054,.029)*g(z,1.508,.019)*front
    v.co.y-=.004*pads
    # Taper cheek-to-chin silhouette; retain mouth width and a distinct anterior chin pad.
    jaw=g(z,1.365,.055)*smooth(.040,.085,abs(x))*front
    v.co.x*=1-.15*jaw
    chin=g(x,-.005,.041)*g(z,1.343,.024)*front
    v.co.y-=.007*chin
    # Recede the soft pad beside the chin to expose the mandibular angle.
    v.co.y+=.008*g(abs(x),.075,.030)*g(z,1.350,.036)*front
body.data.update()
changed={v.index for v in body.data.vertices if (v.co-old[v.index]).length>1e-8}
normal_vertices=set(changed)
for f in body.data.polygons:
    if any(i in changed for i in f.vertices):normal_vertices.update(f.vertices)
if body.data.has_custom_normals:
    body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops));auto=[n.vector.copy() for n in body.data.corner_normals]
    body.data.normals_split_custom_set([auto[i] if l.vertex_index in normal_vertices else normals[i] for i,l in enumerate(body.data.loops)])
assert changed and all(1.30<old[i].z<1.56 for i in changed)
reversals=[]
for f in body.data.polygons:
    a,b,c=f.vertices[:3];before=(old[b]-old[a]).cross(old[c]-old[a]);after=(body.data.vertices[b].co-body.data.vertices[a].co).cross(body.data.vertices[c].co-body.data.vertices[a].co)
    if before.length>1e-10 and after.length>1e-10 and before.dot(after)<0:reversals.append(f.index)
assert not reversals,('local face inversions',reversals)
arm.animation_data.action=bpy.data.actions['Standing'];arm.animation_data.action_slot=arm.animation_data.action.slots[0];scene.frame_set(1)
for o in scene.objects:o.select_set(o in [body,arm,sword])
bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'goblin_anatomy_r5.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'goblin_anatomy_r5.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_rest_position_armature=True,export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_anim_single_armature=True,export_influence_nb=4,export_all_influences=False,export_animations=True,export_yup=True,export_apply=True,export_tangents=True,export_texcoords=True,export_normals=True,export_extras=True,export_image_format='AUTO')
report=dict(status='sculpted; visual review pending',base_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),master_sha256=hashlib.sha256((OUT/'goblin_anatomy_r5.blend').read_bytes()).hexdigest(),glb_sha256=hashlib.sha256((OUT/'goblin_anatomy_r5.glb').read_bytes()).hexdigest(),changed_vertices=len(changed),largest_displacement_m=max((body.data.vertices[i].co-old[i]).length for i in changed),local_normal_reversals=reversals,changes=['Retract excessive supraorbital projection; preserve recessed eyes and eyelid rim.','Taper the rounded cheek-to-chin outline, retain wide mouth and define the central chin.'],unchanged=['neck/body/limbs and armor geometry','all weights','skeleton hierarchy/rest','all nine animation curves','UVs and embedded textures','sword'])
(OUT/'revision.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
