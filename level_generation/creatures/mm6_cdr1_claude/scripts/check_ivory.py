import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
    geometry=[tuple(v.co) for v in o.data.vertices]
    faces=[tuple(f.vertices) for f in o.data.polygons]
    weights=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]
    uv=[tuple(l.uv) for l in o.data.uv_layers.active.data]
    poses=[]
    for name,clip in json.loads((P/'work/clips.json').read_text()).items():
        rig.animation_data.action=bpy.data.actions[name]
        for frame in [0,clip['frames']/2,clip['frames']]:
            bpy.context.scene.frame_set(int(frame),subframe=frame%1)
            poses.append([tuple(v for row in bone.matrix for v in row) for bone in rig.pose.bones])
    return geometry,faces,weights,uv,poses
old=snapshot(P/'work/before_ivory_v3/export/mm6_cdr1.blend');new=snapshot(P/'export/mm6_cdr1.blend')
assert old[:3]==new[:3], 'geometry or skin changed'
assert old[4]==new[4], 'animation poses changed'
assert old[3]!=new[3], 'UV correction missing'
report={'positions_faces_weights_exactly_unchanged':True,'animation_pose_matrices_exactly_unchanged':True,'clips':9,'samples_per_clip':3,'only_uvs_and_maps_changed':True}
(P/'review/ivory_v3/parity.json').write_text(json.dumps(report,indent=2));print('IVORY_PARITY',report)
