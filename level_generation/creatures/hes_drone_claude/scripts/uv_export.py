"""UVs on the clean master and the neutral upload for the Meshy retexture.
Body and tendons: Smart UV Project + pack, squeezed into v 0.125..1 (the strip v < 0.125 is reserved: the lens dome
at u 0..0.125 is mapped planar there and painted procedurally later; the tier gear's UVs go to the rest of the
strip). Reads work/clean_v1.blend, saves work/uv_v1.blend and texturing/hdr_neutral_upload.glb."""
import bpy, bmesh, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
mesh = bpy.data.objects['HDR']
STRIP = 0.125
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
part = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', part)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh.data)
for f in bm.faces:
    f.select = bool(part[f.index] != 4)
bmesh.update_edit_mesh(mesh.data)
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
# Smart UV leaves hundreds of one- and two-triangle islands on the thin decimated tubes: turn the islands into seams,
# clear the seams of every island smaller than MIN_FACES (so they merge into a neighbour) and unwrap again (angle based).
MIN_FACES = 6
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.seams_from_islands()
for rnd in range(3):
    bm = bmesh.from_edit_mesh(mesh.data)
    faces = [f for f in bm.faces if f.select]
    seen = set(); small = 0
    for f in faces:
        if f.index in seen:
            continue
        stack = [f]; island = []; seen.add(f.index)
        while stack:
            g = stack.pop(); island.append(g)
            for e in g.edges:
                if e.seam:
                    continue
                for h in e.link_faces:
                    if h.select and h.index not in seen:
                        seen.add(h.index); stack.append(h)
        if len(island) < MIN_FACES:
            small += 1
            for g in island:
                for e in g.edges:
                    e.seam = False
    bmesh.update_edit_mesh(mesh.data)
    print('UV round', rnd, 'small islands', small)
    if small == 0:
        break
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.003)
bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
bm = bmesh.from_edit_mesh(mesh.data); uvl = bm.loops.layers.uv.active
lens_co = np.array([[l.vert.co.x, l.vert.co.z] for f in bm.faces if part[f.index] == 4 for l in f.loops])
lo, hi = lens_co.min(0), lens_co.max(0); span = (hi - lo).max()
for f in bm.faces:
    for l in f.loops:
        if part[f.index] == 4:   # planar front projection into the strip's first square (u to the drone's right)
            x, z = (l.vert.co.x - lo[0]) / span, (l.vert.co.z - lo[1]) / span
            l[uvl].uv = (0.008 + (1 - x) * (STRIP - 0.016), 0.008 + z * (STRIP - 0.016))
        else:
            u, v = l[uvl].uv
            l[uvl].uv = (u, STRIP + v * (1 - STRIP))
bmesh.update_edit_mesh(mesh.data)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_v1.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'hdr_neutral_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UV done, tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))
