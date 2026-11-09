"""Standing-pose height to the helmet crest (body + helmet, wings excluded) from the textured master and the fitted
helmet, for the binding scale. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
act = bpy.data.actions['Standing']; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(0)
deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
gv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['garment'].data.foreach_get('value', gv)
z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['HelmetMesh']
hm = dst.objects[0]; HF = json.load(open(os.path.join(HERE, 'work', 'helmet_fit.json')))
sc_ = HF['scale'] if isinstance(HF['scale'], list) else [HF['scale']] * 3
H = np.array([tuple(Vector(HF['offset']) + Vector([v.co[k] * sc_[k] for k in range(3)])) for v in hm.data.vertices])
# the helmet rides on B_Head: transform from rest to the posed head
hb = rig.pose.bones['Helmet']; M = rig.matrix_world @ hb.matrix @ rig.data.bones['Helmet'].matrix_local.inverted()
Hz = np.array([(M @ Vector(p)).z for p in H])
print('STANDH body (no wings) top', round(float(z[gv != 5].max()), 3), 'helmet crest top', round(float(Hz.max()), 3),
      'soles', round(float(z.min()), 3))
