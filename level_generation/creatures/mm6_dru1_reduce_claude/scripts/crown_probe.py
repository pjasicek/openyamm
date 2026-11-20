"""Which surface is the dark band above the hair crown (viewer, Standing 0)? Ray-casts from a front camera grid over
the band and reports the first-hit face's class (hood outer/inner by normal vs the head centre, hair, skin), its
base colour (viewer GLB = ramps baked) and the angle between its shading normal and the view direction.
Usage: blender -b -P crown_probe.py -- <viewer glb>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
body = next(o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name and o.data.uv_layers)
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
me.transform(body.matrix_world); me.calc_loop_triangles()
bsdf = next(n for n in body.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
im = bsdf.inputs['Base Color'].links[0].from_node.image
B = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels); H, W = B.shape[:2]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); tree = BVHTree.FromBMesh(bm)
uv = me.uv_layers.active.data
head = rig.matrix_world @ next(b for b in rig.pose.bones if b.name.endswith('Head')).head
res = {}
for z in np.arange(head.z + .15, head.z + .30, .01):
    row = []
    for x in np.arange(-.06, .061, .02):
        o = Vector((x, -1, z)); hit = tree.ray_cast(o, Vector((0, 1, 0)))
        if hit[0] is None: row.append('   .   '); continue
        f = me.polygons[hit[2]]
        u = sum(uv[l].uv[0] for l in f.loop_indices) / f.loop_total; v = sum(uv[l].uv[1] for l in f.loop_indices) / f.loop_total
        col = B[min(H - 1, int(v * H)), min(W - 1, int(u * W)), :3]
        nrm = sum((me.loops[l].normal for l in f.loop_indices), Vector()).normalized()
        inward = nrm.dot((head - hit[0]).normalized()) > 0
        lum = float(col @ np.array([.2126, .7152, .0722]))
        k = 'H' if u > .5 else 'b'
        green = col[1] > col[0] * 1.1
        tag = ('hood' if green else ('skin' if col[0] > .5 and col[2] > col[0] * .35 else 'hair')) + ('-in' if inward else '')
        row.append(f'{tag:8s}{lum:.2f} n{nrm.y:+.1f}')
    print(f'z{z - head.z:+.2f}', ' | '.join(row))
