"""Inspect the immutable Meshy return; save a normalized authoring copy and clay views."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert meshes, 'Meshy returned no mesh'
for o in list(bpy.data.objects):
    if o not in meshes:
        bpy.data.objects.remove(o, do_unlink=True)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
m = bpy.context.object
m.name = m.data.name = 'Wyvern'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in m.data.vertices])
assert np.isfinite(co).all()
# Keep the service orientation until the clay views establish its forward axis.
m.data.materials.clear()
for f in m.data.polygons:
    f.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/body_import.blend'))
np.save(P / 'work/body_vertices.npy', co)
m.data.calc_loop_triangles()
tri = np.array([f.vertices[:] for f in m.data.loop_triangles])
np.save(P / 'work/body_triangles.npy', tri)
lo, hi = co.min(0), co.max(0)
report = {'vertices':len(co), 'triangles':len(tri), 'bounds':[lo.tolist(),hi.tolist()]}
(P / 'review/geometry_initial.json').write_text(json.dumps(report,indent=2)+'\n')
print('GEOMETRY',report,flush=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.48,0.58,0.5)
sc.render.resolution_x = 1200
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
cam = bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = float(max(hi-lo))*1.15
sc.camera=cam
centre = Vector((lo+hi)/2)
for name,direction in [('front',(0,-1,0)),('side',(1,0,0)),('top',(0,0,1)),('quarter',(1,-1,0.5)),('back',(0,1,0))]:
    cam.location = centre + Vector(direction).normalized()*4
    cam.rotation_euler = (centre-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath = str(P / ('review/clay_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
print('CLAY_COMPLETE',flush=True)
