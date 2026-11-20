"""Meshy auto-rig joints mapped into our step1 frame (bounding boxes of the two meshes matched: uniform scale from the
height, translation from the box centre/bottom). Writes work/meshy_joints.json with source-named keys where a
counterpart exists. Args: -- <rigged glb> <our blend>"""
import bpy, sys, os, json
import numpy as np
rig_glb, ours = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ours))
oc = np.array([tuple(bpy.data.objects['Body'].matrix_world @ v.co) for v in bpy.data.objects['Body'].data.vertices])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(rig_glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
deps = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(deps); me = ev.to_mesh()
mc = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices]); ev.to_mesh_clear()
s = (oc[:, 2].max() - oc[:, 2].min()) / (mc[:, 2].max() - mc[:, 2].min())
cen = lambda c: np.array([(c[:, 0].max() + c[:, 0].min()) / 2, (c[:, 1].max() + c[:, 1].min()) / 2, c[:, 2].min()])
t = cen(oc) - cen(mc) * s
print('MAP scale', round(s, 4), 'names', [b.name for b in arm.data.bones][:30])
MAP = {'Hips': 'Pelvis', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side, s_ in (('Left', 'L'), ('Right', 'R')):
    MAP.update({f'{side}Shoulder': f'{s_}_Clavicle', f'{side}Arm': f'{s_}_UpperArm', f'{side}ForeArm': f'{s_}_Forearm',
                f'{side}Hand': f'{s_}_Hand', f'{side}UpLeg': f'{s_}_Thigh', f'{side}Leg': f'{s_}_Calf',
                f'{side}Foot': f'{s_}_Foot', f'{side}ToeBase': f'{s_}_Toe0'})
J = {}
for b in arm.data.bones:
    if b.name in MAP:
        J[MAP[b.name]] = [round(float(x), 5) for x in np.array(arm.matrix_world @ b.head_local) * s + t]
json.dump({'joints': J, 'all_bones': [b.name for b in arm.data.bones]}, open(os.path.join(HERE, 'work', 'meshy_joints.json'), 'w'), indent=1)
print('MESHY joints', len(J))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
