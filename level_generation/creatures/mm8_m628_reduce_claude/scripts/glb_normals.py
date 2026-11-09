"""Custom normals for a ladder candidate from an UNWELDED import of the installed GLB (m628: the installed normals
are not plain smooth normals; the skull's softened sockets and the hard edges of the hood and bones are authored).
The welded work/source.blend must not be the source (its weld scrambles custom normals; RETOPOLOGY_PLAYBOOK.md MM8
batch lessons). Both meshes in the rest pose, nearest-face-interpolated corner normals.
Usage: REA_CAND=Cand_84 blender -b -P glb_normals.py -- <blend in work/> <installed glb> <node>  (saves the blend in place)"""
import os, sys, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, glb, node = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ['REA_CAND']]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
new = [o for o in bpy.data.objects if o not in before]
ref = next(o for o in new if o.type == 'MESH' and o.name.startswith(node))
for o in new:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for b in o.pose.bones:
            b.matrix_basis.identity()
for m in list(ref.modifiers):
    ref.modifiers.remove(m)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); bpy.context.view_layer.objects.active = cand
arm = [m for m in cand.modifiers if m.type == 'ARMATURE']
for m in arm:
    m.show_viewport = False
if os.environ.get('REA_NORMAL_PIECES'):
    # only the listed pieces (connected parts of the candidate whose centre lies within 2 cm of a given point)
    import numpy as np
    me = cand.data; parent = list(range(len(me.vertices)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    pc = np.array([find(i) for i in range(len(me.vertices))]); co = np.array([v.co[:] for v in me.vertices])
    grp = cand.vertex_groups.new(name='NormalMask'); picked = []
    for c in [tuple(float(x) for x in t.split(',')) for t in os.environ['REA_NORMAL_PIECES'].split(';')]:
        for p in np.unique(pc):
            m = pc == p
            if m.sum() > 100 and np.linalg.norm(co[m].mean(0) - np.array(c)) < .02:
                grp.add(np.flatnonzero(m).tolist(), 1.0, 'REPLACE'); picked.append(int(m.sum()))
    print('NORMAL pieces', picked)
dt = cand.modifiers.new('N', 'DATA_TRANSFER'); dt.object = ref; dt.use_loop_data = True
dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'; dt.use_object_transform = True
if os.environ.get('REA_NORMAL_PIECES'):
    dt.vertex_group = 'NormalMask'
while cand.modifiers[0] != dt:
    bpy.ops.object.modifier_move_up(modifier=dt.name)
bpy.ops.object.modifier_apply(modifier=dt.name)
for m in arm:
    m.show_viewport = True
for o in new:
    bpy.data.objects.remove(o, do_unlink=True)
if cand.vertex_groups.get('NormalMask'):
    cand.vertex_groups.remove(cand.vertex_groups['NormalMask'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', blend))
print('GLBNORMALS', cand.name, len(cand.data.polygons))
