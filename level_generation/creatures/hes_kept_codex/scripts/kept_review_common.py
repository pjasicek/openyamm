"""CPU-only adaptation of the playbook's common render_views for local rig review."""
import bpy,math
from mathutils import Vector

def ortho_camera(name, location, rotation, scale):
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale
    cam=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(cam)
    cam.location=location;cam.rotation_euler=rotation;return cam

def workbench_clay(scene):
    # The shared X-ray callers use this name; use CPU Cycles on this host.
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('RigReview');scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.4,.4,.4,1);bg.inputs[1].default_value=.8
    for mat in bpy.data.materials:
        if not mat.users:continue
        colour=tuple(mat.diffuse_color);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear()
        out=nodes.new('ShaderNodeOutputMaterial');diff=nodes.new('ShaderNodeBsdfDiffuse')
        diff.inputs['Color'].default_value=colour
        if colour[3]<1:
            tr=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
            mix.inputs[0].default_value=.45;mat.node_tree.links.new(tr.outputs[0],mix.inputs[1]);mat.node_tree.links.new(diff.outputs[0],mix.inputs[2])
            mat.node_tree.links.new(mix.outputs[0],out.inputs['Surface'])
        else:mat.node_tree.links.new(diff.outputs[0],out.inputs['Surface'])
def render_views(path_prefix, center_z, height, views=('front', 'left', 'back', 'right'), distance=6.0,
                 resolution=(512, 768), target=(0.0, 0.0)):
    """Orthographic turnaround. Character faces -Y (Blender), so 'front' camera sits at -Y."""
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    angles = {'front': 0.0, 'left': 90.0, 'back': 180.0, 'right': -90.0, 'three_quarter': 35.0, 'side60': 60.0, 'rside60': -60.0}
    outputs = []
    for view in views:
        a = math.radians(angles[view])
        # Rotate camera around Z; 'left' shows the character's left side (camera at -X... character left is +X).
        x = target[0] + math.sin(a) * distance
        y = target[1] - math.cos(a) * distance
        cam = ortho_camera('cam_' + view, (x, y, center_z), (math.radians(90), 0, a), height)
        scene.camera = cam
        scene.render.filepath = f'{path_prefix}_{view}.png'
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)
        bpy.data.objects.remove(cam, do_unlink=True)
    return outputs
