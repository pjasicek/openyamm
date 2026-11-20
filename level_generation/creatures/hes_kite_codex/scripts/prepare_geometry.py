"""Repair the multiview return into a neutral four-wing Ashkite; preserve the original download."""
import bpy, bmesh, json, math, os, sys, traceback
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix

P = Path(__file__).resolve().parents[1]

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(P / "meshy/body_geometry_multiview_v2/model_urls_glb.glb"))
    src = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = src
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(src.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(src.data); bm.free()
    src.data.calc_loop_triangles()
    co = np.array([tuple(v.co) for v in src.data.vertices])
    faces = np.array([tuple(t.vertices) for t in src.data.loop_triangles])
    mid = co[faces].mean(1)
    wing = (abs(mid[:,0]) > .07) & (mid[:,2] > -.105)
    assert wing.sum() > 1000 and (~wing).sum() > 1000
    groups = {'Body': faces[~wing], 'Front_L': faces[wing & (mid[:,0] > 0)],
              'Front_R': faces[wing & (mid[:,0] < 0)]}
    material = bpy.data.materials.new('Ashkite'); material.use_nodes = True
    material.diffuse_color = (.35,.31,.26,1)
    objects=[]
    for name, fs in groups.items():
        names = [name, name.replace('Front','Rear')] if name != 'Body' else [name]
        for part in names:
            used = np.unique(fs); lookup={int(v):i for i,v in enumerate(used)}
            vs=[]
            for original in co[used]:
                v=Vector(original)
                # Remove the baked upstroke about the measured leading-edge root, feathering through the shoulder.
                if v.z > -.13 and abs(v.x) > .06:
                    sign=1 if v.x>0 else -1
                    root=Vector((sign*.07,-.205,-.07))
                    weight=min(1,max(0,(abs(v.x)-.06)/.08))
                    rotated=root+Matrix.Rotation(math.radians(sign*34),3,'Y')@(v-root)
                    v=v.lerp(rotated,weight)
                if part.startswith('Rear'):
                    sign=1 if part.endswith('L') else -1
                    root=Vector((sign*.07,-.205,-.07))
                    offset=v-root
                    offset.x*=.83; offset.y*=.72; offset.z*=.83
                    v=Vector((sign*.065,-.045,-.105))+Matrix.Rotation(math.radians(sign*20),3,'Z')@offset
                vs.append(tuple(v))
            me=bpy.data.meshes.new(part); me.from_pydata(vs,[],[[lookup[int(v)] for v in f] for f in fs]); me.update()
            obj=bpy.data.objects.new(part,me); bpy.context.collection.objects.link(obj); objects.append(obj)
            obj.data.materials.append(material)
            vg=obj.vertex_groups.new(name='part_'+part); vg.add(list(range(len(vs))),1,'REPLACE')
    bpy.data.objects.remove(src,do_unlink=True)
    for obj in objects:
        for face in obj.data.polygons: face.use_smooth=True
    # Add a short hooked A barb. Larger venom sac and spurs are separate B/C attachments later.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=(0,.656,-.13))
    barb=bpy.context.object; barb.name='TailBarb'; barb.scale=(.013,.035,.012)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    barb.data.materials.append(material)
    vg=barb.vertex_groups.new(name='part_Body'); vg.add(list(range(len(barb.data.vertices))),1,'REPLACE')
    objects.append(barb)
    for obj in bpy.context.scene.objects: obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.join()
    body=bpy.context.object; body.name=body.data.name='Ashkite'
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    before=sum(len(f.vertices)-2 for f in body.data.polygons)
    # Protect the hooked head and teeth; reduce low-curvature torso and membrane surfaces first.
    keep=body.vertex_groups.new(name='reduction')
    for v in body.data.vertices:
        w=0 if v.co.y < -.52 else 1
        keep.add([v.index],w,'REPLACE')
    mod=body.modifiers.new('Surface budget','DECIMATE'); mod.ratio=.70
    mod.vertex_group=keep.name; mod.vertex_group_factor=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    body.vertex_groups.remove(body.vertex_groups['reduction'])
    # Metres here are provisional. Final scale is calibrated by projected Fly silhouette area.
    for v in body.data.vertices: v.co*=1.25
    low=min(v.co.z for v in body.data.vertices)
    for v in body.data.vertices: v.co.z-=low
    after=sum(len(f.vertices)-2 for f in body.data.polygons)
    assert 3000 < after <= 14500, after
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v3.blend'))
    bpy.ops.export_scene.gltf(filepath=str(P/'work/geometry_v3.glb'),use_selection=True,export_format='GLB',
                              export_animations=False,export_skins=False,export_attributes=False)
    report={'source':'body_geometry_multiview_v2','triangles_before_reduction':before,'triangles':after,
            'parts':[g.name for g in body.vertex_groups], 'scale_provisional':1.25,'ground_translation':-low,
            'raw_wing_root':[.07,-.205,-.07], 'raw_rear_root':[.065,-.045,-.105],
            'rest_wing_lower_degrees':34,'rear_span_scale':.83,'rear_chord_scale':.72,'rear_sweep_degrees':20}
    (P/'review/geometry_v3.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

try:
    main()
except BaseException:
    traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
