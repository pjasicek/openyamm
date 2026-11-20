"""Side-by-side: the source character (its own mesh, turned to face -Y, scaled to our height) and our rig at the same clip
time, both with the stand-in sword on the right hand. Renders front/right/three-quarter full body and right-hand
close-ups. Args: -- <our blend> <set glb> <clip> <our action> <time s> <out prefix>"""
import bpy, sys, os, math, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, sword_standin
blend, glb, clip, action, t, out = sys.argv[sys.argv.index('--') + 1:]
t = float(t)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
new = set(bpy.data.objects) - before
src = next(o for o in new if o.type == 'ARMATURE')
for o in new:
    if o.type == 'MESH' and o.parent is not src:
        o.hide_render = True
sa = {x.name.split('@')[-1].split('|')[-1]: x for x in set(bpy.data.actions) - acts_before}[clip]
src.animation_data.action = sa
if getattr(sa, 'slots', None) is not None and len(sa.slots):
    src.animation_data.action_slot = sa.slots[0]
H_src = 2.5766; H_our = 1.7
src.rotation_mode = 'XYZ'; src.rotation_euler = (0, 0, math.pi)
s = src.scale[0] * H_our / H_src; src.scale = (s, s, s)
src.location = (0.9, 0, 0)
sw_our = sword_standin.add_sword(rig)
# source stand-in: same grip in the source hand frame (unscaled source units -> our scale)
g = json.load(open(os.path.join(sword_standin.HERE, 'work', 'grip_source.json')))
import bmesh
me = sw_our.data.copy(); sw_src = bpy.data.objects.new('srcsword', me); bpy.context.scene.collection.objects.link(sw_src)
bpy.context.scene.frame_set(int(t * 24), subframe=(t * 24) % 1)
# source action at 30 fps in its own frame numbering
f_src = sa.frame_range[0] + t * 30
bpy.context.scene.frame_set(int(f_src), subframe=f_src % 1)
src_pose = {pb.name: pb.matrix.copy() for pb in src.pose.bones}
bpy.context.scene.frame_set(int(t * 24), subframe=(t * 24) % 1)
# the scene frame now drives our action; hold the source at its own time by keying nothing: re-evaluate source pose
for pb in src.pose.bones:
    pb.matrix_basis = Matrix()
src.animation_data.action = None
for n, m in src_pose.items():
    src.pose.bones[n].matrix = m
    bpy.context.view_layer.update()
sword_standin.place(sw_our, rig)
mh = src.matrix_world @ src.pose.bones['B_R_Hand'].matrix
loc, rot, _ = mh.decompose()
# grip centre in source units: our stand-in was built with our hand scale; rebuild the source one at the source scale
ho = (rig.data.bones['B_R_Hand'].head_local - rig.data.bones['B_R_Forearm'].head_local).length
srcrest = json.load(open(os.path.join(sword_standin.HERE, 'work', 'source_rest.json')))
hs = (Vector(srcrest['B_R_Hand']['head']) - Vector(srcrest['B_R_Forearm']['head'])).length
k = (hs * H_our / H_src) / ho
sw_src.matrix_world = Matrix.Translation(loc) @ rot.to_matrix().to_4x4() @ Matrix.Scale(k, 4)
scene = bpy.context.scene; common.workbench_clay(scene)
common.render_views(out, 0.95, 2.0, views=('front', 'right', 'three_quarter'), resolution=(700, 640), target=(0.45, 0))
wr = rig.matrix_world @ rig.pose.bones['B_R_Hand'].head
ws = src.matrix_world @ src.pose.bones['B_R_Hand'].head
common.render_views(out + '_ourhand', wr.z, 0.35, views=('front', 'right'), resolution=(350, 350), target=(wr.x, wr.y))
common.render_views(out + '_srchand', ws.z, 0.35, views=('front', 'right'), resolution=(350, 350), target=(ws.x, ws.y))
