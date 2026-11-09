"""Native Ogre cleaver/scimitar, measured from ogrstda2; rigid bone and atlas swatches."""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]


def add_sword(rig):
    grip = json.loads((PROJECT/'work/grip_pose.json').read_text())
    h = rig.data.bones['B_R_Hand'].matrix_local
    c = h @ Vector(grip['handle_centre_hand_local'])
    axis = (h.to_3x3() @ Vector(grip['handle_axis_hand_local'])).normalized()
    side = rig.data.bones['B_R_Finger2'].head_local - c
    side = (side - axis * side.dot(axis)).normalized()
    roll = math.radians(float(os.environ.get('BLADE_ROLL_DEG', '45')))
    side = (side * math.cos(roll) + axis.cross(side) * math.sin(roll)).normalized()
    flat = axis.cross(side)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    bone = rig.data.edit_bones.get('Sword') or rig.data.edit_bones.new('Sword')
    bone.head = c; bone.tail = c + axis * 0.15
    bone.parent = rig.data.edit_bones['B_R_Hand']; bone.align_roll(flat)
    bpy.ops.object.mode_set(mode='OBJECT')
    verts, faces, classes = [], [], []

    def point(a, edge, thickness):
        return tuple(c + axis * a + side * edge + flat * thickness)

    def face(indices, material):
        faces.append(indices); classes.append(material)

    # Five-sided blade section gives a real cutting bevel, narrow spine and broad flat.
    # The native blade widens at its clipped shoulder and sweeps toward its pointed back edge.
    profile = [(0, 0, .023, .018), (.18, -.006, .027, .018), (.40, -.018, .035, .020),
               (.58, -.034, .055, .025), (.66, -.043, .058, .018),
               (.71, -.052, .076, .025), (.78, -.067, .077, .027),
               (.86, -.088, .065, .028), (.92, -.110, .035, .020)]
    rings = []
    for t, bend, width, back in profile:
        a = .085 + .74 * t
        thick = .005 * (1 - .4*t)
        rings.append(len(verts))
        verts += [point(a,bend+width,0), point(a,bend+width*.45,thick),
                  point(a,bend-back,thick*.6), point(a,bend-back,-thick*.6),
                  point(a,bend+width*.45,-thick)]
    for r0,r1 in zip(rings[:-1],rings[1:]):
        for j in range(5):
            face((r0+j,r1+j,r1+(j+1)%5,r0+(j+1)%5),'edge' if j in (0,4) else 'blade')
    tip=len(verts); verts.append(point(.825,-.16,0))
    for j in range(5):
        face((rings[-1]+j,tip,rings[-1]+(j+1)%5),'edge' if j in (0,4) else 'blade')
    face(tuple(rings[0]+j for j in reversed(range(5))),'blade')

    def tube(points, radii, material, sides=12):
        starts=[]
        for (a,e),radius in zip(points,radii):
            starts.append(len(verts))
            verts.extend(point(a,e+radius*math.cos(2*math.pi*j/sides),radius*math.sin(2*math.pi*j/sides))
                         for j in range(sides))
        for r0,r1 in zip(starts[:-1],starts[1:]):
            for j in range(sides): face((r0+j,r1+j,r1+(j+1)%sides,r0+(j+1)%sides),material)
        face(tuple(starts[0]+j for j in reversed(range(sides))),material)
        face(tuple(starts[-1]+j for j in range(sides)),material)

    tube([(-.075,0),(.065,0)],[grip['radius']]*2,'grip')
    tube([(-.105,0),(-.098,0),(-.085,0),(-.075,0)],[.008,.025,.025,.014],'gold')
    # Native small straight crossguard; no goblin knuckle bow or decorative gems.
    start=len(verts)
    verts.extend(point(a,e,t) for a in (.062,.080) for e in (-.068,.068) for t in (-.014,.014))
    for q in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):
        face(tuple(start+i for i in q),'gold')
    mesh=bpy.data.meshes.new('SwordMesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    sword=bpy.data.objects.new('SwordMesh',mesh); bpy.context.scene.collection.objects.link(sword)
    sword.vertex_groups.new(name='Sword').add(list(range(len(verts))),1,'REPLACE')
    sword.parent=rig; modifier=sword.modifiers.new('Armature','ARMATURE');modifier.object=rig
    swatches=PROJECT/'textures/ogr_sword_swatches.json'
    if swatches.exists():
        sw=json.loads(swatches.read_text());uv=mesh.uv_layers.new(name='UVMap').data
        for polygon,kind in zip(mesh.polygons,classes):
            u,v,r=sw[kind]
            for j,li in enumerate(polygon.loop_indices):
                a=2*math.pi*j/len(polygon.loop_indices);uv[li].uv=(u+r*math.cos(a),v+r*math.sin(a))
    assert min(p.area for p in mesh.polygons)>1e-8
    print('OGRE_SWORD',sum(len(f)-2 for f in faces),'tris', 'radius',grip['radius'])
    return sword
