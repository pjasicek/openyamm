"""Render the colour proposal (work/proposal/, colour_proposal.py) on the Noble assembly: one three-quarter front view
per candidate (Noble_Flight frame 30), its skin and carapace textures swapped in; tiles review/proposal/<key>.png.
Args: none"""
import bpy, os, sys, json, math
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work', 'assembly_noble.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
cands = json.load(open(os.path.join(P, 'work', 'proposal', 'candidates.json')))
def node(mat):
    return next(n for n in bpy.data.materials[mat].node_tree.nodes if n.type == 'TEX_IMAGE' and any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links))
NODES = {'body': node('OV_Body_A'), 'head': node('OV_Head_A'), 'plate': node('NB_Plate')}
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 520; sc.render.resolution_y = 640
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.32, 0.34, 1)
for name, rot, en in [('K', (50, 0, -30), 3.0), ('F', (70, 0, 140), 1.2)]:
    L = bpy.data.lights.new(name, 'SUN'); L.energy = en; o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
    o.rotation_euler = [math.radians(x) for x in rot]
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0; d = Vector((0.55, -0.83, 0.1)).normalized()
cam.location = Vector((0, 0, 0.95)) + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
act = bpy.data.actions['Noble_Flight']; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
sc.frame_set(30)
os.makedirs(os.path.join(P, 'review', 'proposal'), exist_ok=True)
for c in cands:
    for part, n in NODES.items():
        n.image = bpy.data.images.load(os.path.join(P, 'work', 'proposal', f"{c['key']}_{part}.png"), check_existing=False)
    sc.render.filepath = os.path.join(P, 'review', 'proposal', c['key'] + '.png'); bpy.ops.render.render(write_still=True)
print('PROPOSAL_RENDERED'); sys.stdout.flush(); os._exit(0)
