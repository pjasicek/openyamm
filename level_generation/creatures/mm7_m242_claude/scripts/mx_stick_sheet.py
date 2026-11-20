"""G1 clip preview: Mixamo FBX clips (no skin) drawn as stick figures (bone segments as tubes, a 1 m sword stand-in
in the right fist across the palm, out of the thumb side) seen from the front and from the figure's right side,
N frames per clip spread over the clip. One PNG per clip and view. Args: -- <out dir> <frames> <fbx> [<fbx> ...]"""
import bpy, sys, os, math, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
out, n, files = a[0], int(a[1]), a[2:]
os.makedirs(out, exist_ok=True)


def tube(bm, h, t, r):
    v = t - h
    if v.length < 1e-4:
        return
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r * 0.7, depth=v.length)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((h + t) / 2) @ v.to_track_quat('Z', 'Y').to_matrix().to_4x4(),
                        verts=ret['verts'])


for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    f0, f1 = [int(x) for x in arm.animation_data.action.frame_range]
    sc = bpy.context.scene
    frames = [round(f0 + (f1 - f0) * i / max(n - 1, 1)) for i in range(n)]
    pose = []
    for fr in frames:
        sc.frame_set(fr)
        M = arm.matrix_world
        skip = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'End', 'HeadTop')
        segs = [(M @ pb.parent.head, M @ pb.head, 0.06 if ('Spine' in pb.name or 'Hips' in pb.name) else 0.035)
                for pb in arm.pose.bones if pb.parent is not None and not any(k in pb.name for k in skip)]
        segs += [(M @ pb.head, M @ pb.head + (M.to_3x3() @ (pb.matrix.to_3x3() @ Vector((0, 1, 0)))).normalized() * 0.2, 0.08)
                 for pb in arm.pose.bones if pb.name.endswith(':Head')]
        P = {pb.name.split(':')[-1]: M @ pb.head for pb in arm.pose.bones}
        c = (P['RightHandMiddle1'] + P['RightHand']) / 2
        ax = (P['RightHandIndex1'] - P['RightHandPinky1']).normalized()
        segs.append((c - ax * 0.1, c + ax * 1.0, 0.02))
        pose.append((P['Hips'].copy(), segs))
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x, sc.render.resolution_y = 300 * n, 340
    sc.display.shading.background_type = 'VIEWPORT'; sc.display.shading.background_color = (1, 1, 1)
    sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (0.15, 0.2, 0.5)
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2 * n
    cam.location = ((n - 1) * 1.1, -30, 1.05); cam.rotation_euler = (math.pi / 2, 0, 0)
    arm.hide_render = True
    name = os.path.splitext(os.path.basename(f))[0]
    for view, rz in (('front', 0.0), ('side', math.pi / 2)):
        R = Matrix.Rotation(rz, 4, 'Z')
        mesh = bpy.data.meshes.new('stick'); ob = bpy.data.objects.new('stick', mesh); sc.collection.objects.link(ob)
        bm = bmesh.new()
        for k, (hips, segs) in enumerate(pose):
            base = Vector((hips.x, hips.y, 0))
            off = Vector((k * 2.2, 0, 0))
            for h, t, r in segs:
                tube(bm, R @ (h - base) + off, R @ (t - base) + off, r)
            ret = bmesh.ops.create_cube(bm, size=1)
            bmesh.ops.transform(bm, matrix=Matrix.Translation(off) @ Matrix.Diagonal((1.0, 1.0, 0.01, 1)), verts=ret['verts'])
        bm.to_mesh(mesh)
        sc.render.filepath = os.path.join(out, f'{name}_{view}.png'); bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob)
    print('SHEET', name, f0, f1, frames)
