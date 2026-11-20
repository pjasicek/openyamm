"""Run apply() through Blender MCP; add UVs without changing the revision 7 mesh or animation."""
import json
import math
from pathlib import Path

import bpy
import numpy as np

STAGE = Path(__file__).resolve().parent
BASELINE = STAGE.parent/'animations_native_v7_20261005'
# Shared, non-overlapping atlas; uniform fitting preserves each region's projected aspect.
TILES = {
    'body': (.008, .008, .590, .590),
    'head': (.008, .616, .376, .376),
    'right_hand': (.402, .670, .322, .322),
    'left_hand': (.616, .332, .322, .322),
    'feet': (.616, .008, .306, .306),
    'skull_clasp': (.742, .670, .250, .250),
}


def apply():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    obj = scene.objects['Demon_Native_Mesh']
    source = np.load(BASELINE/'source_geometry.npz')
    assert np.array_equal(np.array([v.co for v in obj.data.vertices]), source['vertices'])
    assert np.array_equal(np.array([tuple(p.vertices) for p in obj.data.polygons]), source['faces'])
    assert obj.mode == 'OBJECT'
    obj.data = obj.data.copy()
    obj.data.name = 'Demon_Revision7_Meshy_UV'
    for edge in obj.data.edges:
        edge.use_seam = False
    for layer in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(layer)
    uv = obj.data.uv_layers.new(name='Meshy_Atlas')
    uv.active_render = True
    weights, names, faces = source['weights'], list(source['group_names']), source['faces']
    groups = {
        'head': [i for i,n in enumerate(names) if n in ('mixamorig:Head','mixamorig:HeadTop_End',
                                                       'mixamorig:Neck','Bone_025','headfront')],
        'right_hand': [i for i,n in enumerate(names) if n.startswith('mixamorig:RightHand')],
        'left_hand': [i for i,n in enumerate(names) if n.startswith('mixamorig:LeftHand')],
        'feet': [i for i,n in enumerate(names) if any(n.startswith('mixamorig:'+s+p)
                    for s in ('Right','Left') for p in ('Foot','Toe'))],
        'skull_clasp': [names.index('Bone_024')],
    }
    regions = list(groups)
    scores = np.array([weights[:,indices].sum(axis=1)[faces].mean(axis=1) for indices in groups.values()])
    best = scores.argmax(axis=0)
    labels = np.array([regions[i] if scores[i,j]>.5 else 'body' for j,i in enumerate(best)])
    for other in scene.objects:
        other.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scene.tool_settings.use_uv_select_sync = False
    scene.tool_settings.mesh_select_mode = (False, False, True)
    report = {}
    for region, (x,y,width,height) in TILES.items():
        selected = labels == region
        obj.data.polygons.foreach_set('select', selected)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(45), island_margin=.002,
                                 margin_method='FRACTION', area_weight=.2,
                                 correct_aspect=False, scale_to_bounds=False)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.seams_from_islands(mark_seams=True,mark_sharp=False)
        bpy.ops.uv.unwrap(method='MINIMUM_STRETCH',iterations=30,no_flip=True,
                          margin=.002,margin_method='FRACTION',correct_aspect=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        cut_faces = set()
        # Cut folded charts locally, keeping the rest of the surface's islands intact.
        for attempt in range(6):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.select_all(action='DESELECT')
            bpy.ops.uv.select_overlap()
            bpy.ops.object.mode_set(mode='OBJECT')
            corners = obj.data.attributes['.uv_select_vert'].data
            folded = [p for p in obj.data.polygons if selected[p.index]
                      and any(corners[i].value for i in p.loop_indices)]
            if not folded:
                break
            assert attempt < 5, ('UV chart repair did not converge',region,len(folded))
            for p in folded:
                cut_faces.add(p.index)
                for i in p.loop_indices:
                    obj.data.edges[obj.data.loops[i].edge_index].use_seam = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='MINIMUM_STRETCH',iterations=30,no_flip=True,
                              margin=.002,margin_method='FRACTION',correct_aspect=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=True,rotate_method='ANY',scale=True,merge_overlap=False,
                                shape_method='CONCAVE',margin=.002,margin_method='FRACTION')
        bpy.ops.object.mode_set(mode='OBJECT')
        uv = obj.data.uv_layers['Meshy_Atlas']
        indices = np.array([i for p in obj.data.polygons if selected[p.index] for i in p.loop_indices])
        points = np.array([uv.data[i].uv for i in indices])
        lo,hi = points.min(axis=0),points.max(axis=0)
        scale = min(width/(hi[0]-lo[0]),height/(hi[1]-lo[1]))
        points = (points-(lo+hi)/2)*scale+np.array([x+width/2,y+height/2])
        for i,point in zip(indices,points):
            uv.data[i].uv = point
        report[region] = dict(triangles=int(selected.sum()),tile=[x,y,width,height],
                              chart_method='Smart projection followed by minimum stretch',
                              uniform_uv_scale=float(scale),locally_cut_faces=len(cut_faces))
        print('UV region', region, report[region], flush=True)
    obj.data.polygons.foreach_set('select', np.ones(len(faces),bool))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.uv.select_overlap()
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = obj.data.uv_layers['Meshy_Atlas']
    overlap = sum(int(v.value) for v in obj.data.attributes['.uv_select_vert'].data)
    assert overlap == 0, ('Overlapping UV corners', overlap)
    coords = np.array([loop.uv for loop in uv.data])
    np.savez_compressed(STAGE/'uv_transfer.npz',uv=coords,face_regions=labels,
                        vertices=source['vertices'],faces=faces)
    (STAGE/'uv_regions.json').write_text(json.dumps(dict(regions=report,
        atlas='Meshy_Atlas',uv_overlap_selected_corners=overlap),indent=2)+'\n')
    obj.data.update()
    # Save a separate animated UV master; previous revision exports remain untouched.
    for owned in list(bpy.data.scenes):
        if owned.name.startswith('MM6_Demon_Meshy_Upload'):
            for item in list(owned.objects):
                if len(item.users_scene) == 1:
                    bpy.data.objects.remove(item,do_unlink=True)
            bpy.data.scenes.remove(owned)
    scene.frame_set(0)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(STAGE/'mm6_demon_uv_master.blend'),compress=True)
    # A static rest-space copy has the same indexed topology and per-corner UVs as the master.
    upload_scene = bpy.data.scenes.new('MM6_Demon_Meshy_Upload')
    upload_scene.world = scene.world
    static = bpy.data.objects.new('MM6_Demon_Meshy_Upload',obj.data.copy())
    upload_scene.collection.objects.link(static)
    bpy.context.window.scene = upload_scene
    static.select_set(True)
    bpy.context.view_layer.objects.active = static
    bpy.ops.export_scene.gltf(filepath=str(STAGE/'mm6_demon_meshy_upload.glb'),export_format='GLB',
        use_selection=True,use_active_scene=True,export_animations=False,export_skins=False,
        export_morph=False,export_materials='EXPORT',export_texcoords=True,
        export_normals=True,export_yup=True,export_cameras=False,export_lights=False)
    bpy.context.window.scene = scene
    print('UV master and static Meshy upload exported; original animation preserved.',flush=True)
