"""Clay turnaround + stats of the Smart Topology return."""
import bpy, bmesh, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    print('MESH', o.name, len(me.vertices), 'faces', len(me.polygons), 'tris', tris, 'quads', sum(1 for f in bm.faces if len(f.verts) == 4),
          'nonmanifold edges', nonmanifold, 'uv', len(me.uv_layers), 'islands?')
    bm.free()
lo, hi = common.world_bounds(meshes)
print('BOUNDS', tuple(lo), tuple(hi))
for o in meshes:
    for p in o.data.polygons: p.use_smooth = True
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, 'smart_v1'), (lo.z + hi.z) / 2, (hi.z - lo.z) * 1.05,
                    views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900), target=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
H = hi.z - lo.z
common.render_views(os.path.join(common.REVIEW, 'smart_v1_upper'), hi.z - H * 0.24, H * 0.5, views=('front',), resolution=(800, 800),
                    target=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
scene.display.shading.show_xray = False
bpy.context.scene.display.shading.show_cavity = True
for o in meshes:
    o.show_wire = True
