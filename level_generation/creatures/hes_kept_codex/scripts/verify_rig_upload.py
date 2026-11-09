"""Reimport each actual rig upload, compare oriented triangles, and render its provisional materials."""
import bpy, sys, os, json, struct, hashlib, math
from pathlib import Path
from collections import Counter
import numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]

def geometry():
    triangles = Counter()
    coordinates = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        me = obj.data
        me.calc_loop_triangles()
        co = [tuple(round(float(x), 5) for x in obj.matrix_world @ v.co) for v in me.vertices]
        coordinates.extend(co)
        for tri in me.loop_triangles:
            points = tuple(co[i] for i in tri.vertices)
            triangles[min(points[i:] + points[:i] for i in range(3))] += 1
    return triangles, np.array(coordinates)

revision = 'v2' if 'v2' in sys.argv else 'v1'
rows = []
for sex in (('m',) if revision == 'v2' else ('m', 'f')):
    blend = P/'work'/f'kept_{sex}_clean_{revision}.blend'
    upload = blend.with_suffix('.glb')
    raw = upload.read_bytes()
    assert len(raw) < 100*1024*1024
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    n, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a
    gltf = json.loads(raw[20:20+n])
    assert not gltf.get('skins') and not gltf.get('animations')
    assert len(gltf['images']) == (1 if revision == 'v2' else 2) and all('bufferView' in i for i in gltf['images'])
    for mesh in gltf['meshes']:
        for prim in mesh['primitives']:
            assert prim.get('mode', 4) == 4 and 'TEXCOORD_0' in prim['attributes']
    for mat in gltf['materials']:
        assert not mat.get('doubleSided', False) and mat.get('alphaMode', 'OPAQUE') == 'OPAQUE'
        pbr = mat['pbrMetallicRoughness']
        assert pbr['metallicFactor'] == 0 and abs(pbr['roughnessFactor']-.85) < 1e-5
        assert 'baseColorTexture' in pbr
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    expected, before = geometry()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(upload))
    actual, co = geometry()
    assert actual == expected, f'{sex}: oriented triangle geometry changed in export'
    assert np.isfinite(co).all() and abs(co[:,2].min()) < 1e-5 and abs(co[:,2].max()-1.7) < 1e-5
    assert not any(o.type == 'ARMATURE' for o in bpy.data.objects)
    row = dict(upload=str(upload.relative_to(P)), sha256=hashlib.sha256(raw).hexdigest(),
               bytes=len(raw), triangles=sum(actual.values()), height_m=float(np.ptp(co[:,2])),
               oriented_triangles_match_blend_at_10um=True, embedded_images=len(gltf['images']),
               provisional_textures_only=True, facing='glTF +Z / Blender -Y',
               no_skins_or_animations=True, finite_positions=True, single_sided_opaque=True)
    scene = bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=768 if revision=='v2' else 512;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    for pos,power in [((3,-4,5),500),((-3,-2,3),300),((0,4,4),250)]:
        data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=4
        obj=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(obj);obj.location=pos
        obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.cameras.new('ReviewCamera');camera.type='ORTHO';camera.ortho_scale=1.95
    cam=bpy.data.objects.new('ReviewCamera',camera);scene.collection.objects.link(cam);scene.camera=cam
    out=P/'review/geometry'/(f'{sex}_upload'+('_v2' if revision == 'v2' else ''));out.mkdir(exist_ok=True)
    row['renders']=[]
    for name, angle in [('front',0),('back',180),('quarter',35)]:
        target=Vector((0,0,.85));a=math.radians(angle)
        cam.location=target+Vector((5*math.sin(a),-5*math.cos(a),0))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        output=out/f'{name}.png';scene.render.filepath=str(output)
        bpy.ops.render.render(write_still=True)
        row['renders'].append(str(output.relative_to(P)))
    rows.append(row)
(P/'review/geometry'/('rig_upload_v2_validation.json' if revision == 'v2' else 'rig_upload_validation.json')).write_text(json.dumps({'scope':'Rig service uploads only; final geometry/UV/animation gates pending','uploads':rows},indent=2)+'\n')
print('UPLOADS',json.dumps(rows),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
