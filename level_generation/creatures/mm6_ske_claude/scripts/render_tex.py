"""Textured workbench renders (rest pose or a clip frame): Bone material <- body base colour, Head <- head base colour.
Args: -- <blend> <body png> <head png> <tag> [action frame]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, body_png, head_png, tag = a[:4]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Skeleton_Rig']
if len(a) > 4:
    rig.animation_data_create(); act = bpy.data.actions[a[4]]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(a[5]))


def textured(mat, path):
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    img = nt.nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(os.path.abspath(path))
    nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
    nt.nodes.active = img


textured(bpy.data.materials['Bone'], body_png)
textured(bpy.data.materials['Head'], head_png)
scene = bpy.context.scene; common.workbench_clay(scene, textured=True)
out = os.path.join(common.REVIEW, tag)
common.render_views(out, 0.82, 1.75, views=('front', 'three_quarter', 'left', 'back'), resolution=(420, 840))
common.render_views(out + '_head', 1.45, 0.34, views=('front', 'three_quarter', 'left'), resolution=(420, 420))
