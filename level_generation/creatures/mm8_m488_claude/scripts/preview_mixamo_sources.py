"""G1: preview exact local Mixamo joint motion with an abstract source-joint mannequin."""
from pathlib import Path
import hashlib
import json
import math
import sys
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).parent))
import common
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
lib = repo / 'anim_library/mixamo'
out = p / 'review/motion/mixamo'
out.mkdir(parents=True, exist_ok=True)
report = {}
for name in ['Standard Idle', 'Walk', 'Standard Run', 'Standing Melee Punch']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=str(lib / (name + '.fbx')))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    action = rig.animation_data.action
    assert action is not None and scene.render.fps / scene.render.fps_base == 30
    f0, f1 = action.frame_range
    scene.frame_set(int(f0))
    bones = [b for b in rig.pose.bones if b.parent and not any(x in b.name for x in ('HandThumb','HandIndex','HandMiddle','HandRing','HandPinky'))]
    def point(b):
        return rig.matrix_world @ b.head
    points = [point(b) for b in rig.pose.bones]
    lo = min(v.z for v in points)
    hi = max(v.z for v in points)
    H = hi-lo
    rods = []
    for b in bones:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4)
        o = bpy.context.object
        o.name = b.name + '_display'
        radius = H * (0.055 if any(s in b.name for s in ('Spine','Neck','Head')) else 0.025)
        rods.append((b,o,radius))
    def update():
        for b,o,radius in rods:
            a,z = point(b.parent),point(b)
            d = z-a
            o.location = (a+z)/2
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = d.to_track_quat('Z','Y')
            o.scale = (radius,radius,max(d.length/2,radius))
    common.workbench_clay(scene)
    rows = []
    for view in ('front','left','three_quarter'):
        row=[]
        for i in range(7):
            f=f0+(f1-f0)*i/6
            scene.frame_set(int(f),subframe=f-int(f));update()
            image=common.render_views(str(out/(name.replace(' ','_')+f'_{i}')),(lo+hi)/2,H*1.35,
                                      views=(view,),resolution=(240,380))[0]
            row.append([image,f'{name} {f:.1f}'])
        rows.append(row)
    (out/(name.replace(' ','_')+'.json')).write_text(json.dumps(rows))
    traces={b.name:[] for b in rig.pose.bones if any(s in b.name for s in ('Head','Arm','ForeArm','Hand','Foot'))}
    for f in range(int(f0),int(f1)+1):
        scene.frame_set(f)
        for n in traces:
            b=rig.pose.bones[n];M=rig.matrix_world@b.matrix
            traces[n].append({'frame':f,'head':list(point(b)),'quaternion':list(M.to_quaternion())})
    report[name]={'path':str((lib/(name+'.fbx')).relative_to(repo)),
                  'sha256':hashlib.sha256((lib/(name+'.fbx')).read_bytes()).hexdigest(),
                  'frames':[f0,f1],'fps':30,'duration':(f1-f0)/30,'source_joint_traces':traces,
                  'preview':'Abstract rods follow exact source joints; no target rig retargeting.'}
(out/'sources.json').write_text(json.dumps(report,indent=2)+'\n')
assert len(report)==4
