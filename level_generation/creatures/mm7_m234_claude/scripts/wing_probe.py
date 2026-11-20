"""Find the bat-wing skeleton on the m234 'Wings' object (rest, facing -Y): per side the wrist = the highest strut
vertex (the hooked claw at the top of the leading edge), the root = the wing vertices nearest the back midline, the
elbow = the leading-edge point farthest from the root -> wrist line, and the finger-strut TIPS = local maxima of the
distance from the wrist along the trailing edge (scalloped points), clustered by angle in the wing plane and kept as the
four farthest clusters. Writes work/wing_skeleton.json and review/wing_probe_front.png (points marked).
Args: -- <blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
w = bpy.data.objects['Wings']; me = w.data
co = np.array([tuple(w.matrix_world @ v.co) for v in me.vertices])
pc = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
out = {}
for s, sg in (('L', 1.0), ('R', -1.0)):
    m = co[:, 0] * sg > 0
    strut = m & (pc == 0)                                  # the struts and the arm are on P00; P01/P02 are membranes
    S = co[strut]
    band = (np.abs(S[:, 0]) > 0.4) & (np.abs(S[:, 0]) < 0.8)
    wrist = S[band][np.argmax(S[band][:, 2])]                  # the hooked claw at the top of the arm
    near = S[np.argsort(np.abs(S[:, 0]))[:20]]
    root = near.mean(0)
    mid = (root + wrist) / 2
    elbow = S[np.argmin(np.linalg.norm(S - mid, axis=1))]     # the arm strut nearest the midpoint
    lead = co[m][np.argmax(np.abs(co[m][:, 0]))]               # the leading finger's tip (farthest out)
    # wing plane basis at the wrist: u = outward along the wing (from the root), v = down in the plane
    nrm = np.linalg.svd(co[m] - co[m].mean(0), full_matrices=False)[2][2]
    u = wrist - root; u -= nrm * (u @ nrm); u /= np.linalg.norm(u); v = np.cross(nrm, u)
    if v[2] > 0:
        v = -v
    A = co[m] - wrist; ang = np.degrees(np.arctan2(A @ v, A @ u)); dist = np.linalg.norm(A, axis=1)
    # finger tips: the farthest vertex per 6-degree sector; local maxima of that profile
    sect = np.arange(-30, 181, 6); prof = []
    for a0 in sect:
        k = (ang >= a0) & (ang < a0 + 6) & (dist > 0.25)
        prof.append((float(dist[k].max()), int(np.where(k)[0][np.argmax(dist[k])])) if k.any() else (0.0, -1))
    peaks = [i for i in range(1, len(prof) - 1) if prof[i][0] > 0 and prof[i][0] >= prof[i - 1][0] and prof[i][0] >= prof[i + 1][0]
             and abs(co[m][prof[i][1]][0]) > 0.18 and np.linalg.norm(co[m][prof[i][1]] - lead) > 0.2]
    peaks = sorted(sorted(peaks, key=lambda i: -prof[i][0])[:3], key=lambda i: sect[i])
    tips = [lead] + [co[m][prof[i][1]] for i in peaks]
    out[s] = {'root': root.tolist(), 'elbow': elbow.tolist(), 'wrist': wrist.tolist(), 'tips': [t.tolist() for t in tips],
              'normal': nrm.tolist()}
    print('WINGPROBE', s, 'root', np.round(root, 3), 'elbow', np.round(elbow, 3), 'wrist', np.round(wrist, 3),
          'tips', [np.round(t, 2).tolist() for t in tips], 'tip angles', [sect[i] for i in peaks])
json.dump(out, open(os.path.join(HERE, 'work', 'wing_skeleton.json'), 'w'), indent=1)
# markers
import bmesh
bm = bmesh.new()
for s in out.values():
    for p in [s['root'], s['elbow'], s['wrist']] + s['tips']:
        r = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.03)
        bmesh.ops.translate(bm, verts=r['verts'], vec=Vector(p) + Vector((0, -0.4, 0)))
mk = bpy.data.meshes.new('mk'); bm.to_mesh(mk); o = bpy.data.objects.new('mk', mk); bpy.context.scene.collection.objects.link(o)
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.name not in ('Wings', 'mk', 'Body'):
        ob.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x, sc.render.resolution_y = 1100, 700
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.1; cam.location = (0, -6, 1.2); cam.rotation_euler = (math.pi / 2, 0, 0)
sc.render.filepath = os.path.join(HERE, 'review', 'wing_probe_front.png'); bpy.ops.render.render(write_still=True)
