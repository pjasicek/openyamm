"""Load the Smart Topology ooze, normalise (long horizontal axis along Y, length 1.0 m, bottom at z=0, centred),
report pieces/triangles/extents, save work/ooz_raw.blend and clay renders review/raw_*.png."""
import bpy, bmesh, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/smart_topology_v1/model_urls_glb.glb'))
objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
o.name = 'Ooze'
o.data.name = 'Ooze'
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for e in [x for x in bpy.data.objects if x.type != 'MESH']:
    bpy.data.objects.remove(e, do_unlink=True)
co = np.array([tuple(v.co) for v in o.data.vertices])
ext = np.ptp(co, 0)
print('RAW extents', ext.round(3))
if ext[0] > ext[1]:                                     # long axis along Y
    for v in o.data.vertices:
        v.co = (v.co.y, -v.co.x, v.co.z)
co = np.array([tuple(v.co) for v in o.data.vertices])
s = 1.0 / np.ptp(co[:, 1])
c = (co.max(0) + co.min(0)) / 2
for v in o.data.vertices:
    v.co = ((v.co.x - c[0]) * s, (v.co.y - c[1]) * s, (v.co.z - co[:, 2].min()) * s)
o.data.update()
o.data.materials.clear()
co = np.array([tuple(v.co) for v in o.data.vertices])
bm = bmesh.new(); bm.from_mesh(o.data)
import collections
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    st, comp = [v], []
    seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(comp)
nb = sum(1 for e in bm.edges if e.is_boundary)
bm.free()
print('NORM extents', np.ptp(co, 0).round(3), 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), 'verts', len(co),
      'pieces', len(comps), 'sizes', sorted(len(c) for c in comps)[::-1][:12], 'boundary edges', nb)
for p in o.data.polygons:
    p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'ooz_raw.blend'))
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
o.show_wire = True
common.render_views(os.path.join(common.REVIEW, 'raw'), 0.12, 0.9, views=('front', 'three_quarter', 'left'), resolution=(700, 450))
cam = common.ortho_camera('top', (0, 0, 5), (0, 0, 0), 1.2)
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 700, 700
sc.render.filepath = os.path.join(common.REVIEW, 'raw_top.png')
bpy.ops.render.render(write_still=True)
