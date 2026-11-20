"""Close-up of one wrist in one posed frame, gate-style classes over a lit render: front faces lit grey, back faces red,
holes (only back faces along the ray) yellow. Args: <glb> <out png> <clip> <frame30> <az> <el> <L|R> [size_m 0.22] [res 640]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, CLIP, F30, AZ, EL, SIDE = a[0], a[1], a[2], int(a[3]), float(a[4]), float(a[5]), a[6]
SIZE = float(a[7]) if len(a) > 7 else 0.22; RES = int(a[8]) if len(a) > 8 else 640
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not mesh: bpy.data.objects.remove(o)
twin = mesh.copy(); twin.data = mesh.data.copy(); bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(twin.data); bm.free()
mesh.color = (0.6, 0.6, 0.6, 1); twin.color = (1, 0, 0, 1)
sc = bpy.context.scene; FPS = sc.render.fps / sc.render.fps_base
act = bpy.data.actions[CLIP]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
f = act.frame_range[0] + F30 / 30.0 * FPS; sc.frame_set(int(f), subframe=f % 1.0)
pb = rig.pose.bones[f'Bip01 {SIDE} Hand']; C = rig.matrix_world @ pb.head
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.color_type = 'OBJECT'; sh.show_backface_culling = True
sc.display.render_aa = 'OFF'; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.color_mode = 'RGBA'; sc.render.resolution_x = sc.render.resolution_y = RES
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = SIZE
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
d = Vector((math.sin(math.radians(AZ)) * math.cos(math.radians(EL)), -math.cos(math.radians(AZ)) * math.cos(math.radians(EL)), math.sin(math.radians(EL))))
cam.location = C + d * 3.0; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cd.clip_end = 10
def render(p, light):
    sh.light = light; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p); px = np.array(im.pixels[:], np.float32).reshape(RES, RES, 4); bpy.data.images.remove(im); return px
twin.hide_render = True; p1 = render(OUT + '.a.png', 'FLAT')
p3 = render(OUT + '.c.png', 'STUDIO')
twin.hide_render = False; p2 = render(OUT + '.b.png', 'FLAT')
front = p1[..., 3] > 0.5; anyf = p2[..., 3] > 0.5
red = anyf & (p2[..., 0] > 0.9) & (p2[..., 1] < 0.1); hole = anyf & ~front
img = np.ones((RES, RES, 4), np.float32); img[front] = p3[front]; img[..., 3] = 1
img[red] = (0.85, 0.1, 0.1, 1); img[hole] = (1, 0.85, 0, 1)
out = bpy.data.images.new('o', RES, RES, alpha=True); out.pixels = img.ravel().tolist(); out.filepath_raw = OUT; out.file_format = 'PNG'; out.save()
print('WRIST_ZOOM', OUT, 'hole', int(hole.sum()), 'red', int(red.sum()))
# diagnostics: multi-hit rays through hole pixels (posed mesh, every face): order, facing, material, dominant bone
import os
if os.environ.get('DIAG') == '1' and hole.any():
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); em = ev.to_mesh()
    P = [ev.matrix_world @ v.co for v in em.vertices]
    bvh = BVHTree.FromPolygons(P, [p.vertices[:] for p in em.polygons])
    names = [g.name for g in mesh.vertex_groups]
    def dom(pi):
        cnt = {}
        for vi in em.polygons[pi].vertices:
            gs = mesh.data.vertices[vi].groups
            if len(gs):
                g = max(gs, key=lambda g: g.weight).group; cnt[g] = cnt.get(g, 0) + 1
        return names[max(cnt, key=cnt.get)] if cnt else '-'
    rot = cam.rotation_euler.to_matrix(); right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
    ii, jj = np.nonzero(hole)
    sel = np.linspace(0, len(ii) - 1, 6).astype(int)
    for k in sel:
        i, j = ii[k], jj[k]
        o = cam.location + right * (((j + 0.5) / RES - 0.5) * SIZE) + up * (((i + 0.5) / RES - 0.5) * SIZE)
        seq = []; oo = o.copy()
        for _ in range(8):
            h = bvh.ray_cast(oo, fwd, 10)
            if h[0] is None: break
            pol = em.polygons[h[2]]
            seq.append(('F' if h[1].dot(fwd) < 0 else 'B', h[2], mesh.data.materials[pol.material_index].name[-6:], dom(h[2]), round((h[0] - o).length, 3)))
            oo = h[0] + fwd * 1e-4
        print('DIAG', i, j, seq)
    for k in sel[:1]:
        i, j = ii[k], jj[k]
        o = cam.location + right * (((j + 0.5) / RES - 0.5) * SIZE) + up * (((i + 0.5) / RES - 0.5) * SIZE)
        h = bvh.ray_cast(o, fwd, 10); pol = em.polygons[h[2]]
        print('DIAGFACE', h[2], 'rest verts', [tuple(round(c, 4) for c in mesh.data.vertices[v].co) for v in pol.vertices])
