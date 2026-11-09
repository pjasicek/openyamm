import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=o.data
me.materials.clear();material=bpy.data.materials.new('Phoenix_Upload');material.use_nodes=True;me.materials.append(material)
for face in me.polygons:face.material_index=0
bm=bmesh.new();bm.from_mesh(me);bad=[f for f in bm.faces if f.calc_area()<1e-12];bmesh.ops.delete(bm,geom=bad,context='FACES');bm.to_mesh(me);bm.free()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
me.validate(verbose=True,clean_customdata=False)
for layer in list(me.uv_layers):me.uv_layers.remove(layer)
me.uv_layers.new(name='UVMap')

def overlapping(layer, faces, n=2048):
    """Faces whose UV triangles cover a texel centre another triangle already covers (2048 raster)."""
    me.calc_loop_triangles(); uv = me.uv_layers[layer].data
    owner = np.full((n, n), -1, np.int64); bad = set()
    for t in me.loop_triangles:
        if not faces(me.polygons[t.polygon_index]):
            continue
        a, b2, c = [np.array(uv[l].uv) * n for l in t.loops]
        den = (b2[1] - c[1]) * (a[0] - c[0]) + (c[0] - b2[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        lo = np.maximum(np.floor(np.minimum(np.minimum(a, b2), c)).astype(int), 0)
        hi = np.minimum(np.ceil(np.maximum(np.maximum(a, b2), c)).astype(int), n - 1)
        x, y = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w0 = ((b2[1] - c[1]) * (x - c[0]) + (c[0] - b2[0]) * (y - c[1])) / den
        w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
        m = (w0 > 1e-6) & (w1 > 1e-6) & (1 - w0 - w1 > 1e-6)
        iy, ix = (y[m] - .5).astype(int), (x[m] - .5).astype(int)
        prev = owner[iy, ix]
        if (prev >= 0).any():
            bad.add(t.polygon_index)
            bad.update(int(me.loop_triangles[p].polygon_index) for p in np.unique(prev[prev >= 0]))
        owner[iy, ix] = t.index
    return sorted(bad)


def split_uv_faces(layer,bad):
    uv=me.uv_layers[layer].data
    for fi in bad:
        f=me.polygons[fi];assert len(f.vertices)==3
        p0,p1,p2=[np.array(me.vertices[i].co) for i in f.vertices]
        ex=p1-p0;ex/=np.linalg.norm(ex);ez=np.cross(p1-p0,p2-p0);ez/=np.linalg.norm(ez);ey=np.cross(ez,ex)
        old=np.array([uv[i].uv[:] for i in f.loop_indices]);ua=abs(np.linalg.det(np.column_stack([old[1]-old[0],old[2]-old[0]])))*.5
        density=max(math.sqrt(ua/max(f.area,1e-12)),.2)
        for li,point in zip(f.loop_indices,[p0,p1,p2]):uv[li].uv=(2+fi*2+float((point-p0)@ex)*density,2+float((point-p0)@ey)*density)

def unwrap(layer, faces, margin):
    me.uv_layers.active = me.uv_layers[layer]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = faces(p)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, area_weight=0, correct_aspect=True,
                             scale_to_bounds=False)
    # smart-project charts fold on curved shells (hair, ears): keep its charts as seams, re-unwrap them angle-based
    bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
    b=bmesh.from_edit_mesh(me)
    for e in b.edges:
        if len(e.link_faces)==2:
            h=[all(v.co.y<-.125 for v in f.verts) for f in e.link_faces]
            if h[0]!=h[1]:e.seam=True
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=margin)
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    # folds remain inside curved charts: cut every overlapping triangle into its own chart, re-unwrap, repeat
    for attempt in range(6):
        bpy.ops.object.mode_set(mode='OBJECT')
        bad = overlapping(layer, faces)
        print('UV', layer, 'pass', attempt, 'overlapping faces', len(bad), flush=True)
        if not bad:
            break
        if attempt<2:
            b = bmesh.new(); b.from_mesh(me); b.faces.ensure_lookup_table()
            for fi in bad:
                for e in b.faces[fi].edges:e.seam=True
            b.to_mesh(me);b.free();bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED',fill_holes=True,correct_aspect=True,margin=margin)
        else:
            # Freeze good charts; re-unwrapping the whole shell can reintroduce folds elsewhere.
            split_uv_faces(layer,bad)
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.pack_islands(rotate=True,margin=margin,margin_method='FRACTION',shape_method='CONCAVE')
    else:
        raise RuntimeError(f'{layer}: UV folds remain')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.mark_seam(clear=True)
    bpy.ops.object.mode_set(mode='OBJECT')

unwrap('UVMap',lambda face:True,.003)
# Give the small avian head more texel density within the one body atlas.
uv=me.uv_layers.active.data
for f in me.polygons:
 if all(me.vertices[i].co.y<-.125 for i in f.vertices):
  for li in f.loop_indices:uv[li].uv*=2.5
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.seams_from_islands(mark_seams=True,mark_sharp=False)
bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION',shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
for attempt in range(6):
 bad=overlapping('UVMap',lambda face:True);print('HEAD DENSITY UV',attempt,len(bad),flush=True)
 if not bad:break
 split_uv_faces('UVMap',bad);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION',shape_method='CONCAVE')
 bpy.ops.object.mode_set(mode='OBJECT')
else:raise RuntimeError('UV folds remain after head density')
# Unrigged upload retains the exact reduced positions and UVs.
dup=o.copy();dup.data=me.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
bpy.data.objects.remove(dup,do_unlink=True);bpy.context.view_layer.objects.active=o
rig.animation_data_create();rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
(P/'work/uv_report.json').write_text(json.dumps({'overlap_faces':bad,'atlas_size':2048,'head_density_multiplier':2.5},indent=2)+'\n')
