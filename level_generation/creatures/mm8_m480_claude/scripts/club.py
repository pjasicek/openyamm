"""Assemble the separately generated bone club at the solved right-hand grip."""
from pathlib import Path
import bpy,json
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1]
def add_club(rig):
    with bpy.data.libraries.load(str(p/'work/club.blend'),link=False) as (src,dst):dst.objects=['Club']
    club=dst.objects[0];bpy.context.scene.collection.objects.link(club)
    grip=json.loads((p/'work/grip_pose.json').read_text());shaft=json.loads((p/'work/club_fit.json').read_text())
    center=Vector(grip['handle_centre_hand_local']);axis=Vector(grip['handle_axis_hand_local'])
    origin=Vector((*shaft['grip_xy'],shaft['grip_z']))
    transform=Matrix.Translation(center)@Vector((0,0,1)).rotation_difference(axis).to_matrix().to_4x4()@Matrix.Translation(-origin)
    club.data.transform(rig.data.bones['B_R_Hand'].matrix_local@transform)
    club.matrix_world=rig.matrix_world.copy();club.vertex_groups.clear()
    group=club.vertex_groups.new(name='B_R_Hand');group.add(list(range(len(club.data.vertices))),1,'REPLACE')
    mod=club.modifiers.new('Armature','ARMATURE');mod.object=rig;club.parent=rig
    club['hand_local_transform']=[list(row) for row in transform]
    return club
